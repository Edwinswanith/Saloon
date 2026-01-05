from flask import Blueprint, request, jsonify
from mongoengine import Q
from datetime import datetime, timedelta
from models import DiscountApprovalRequest, ApprovalCode, Bill, Staff, Manager
from utils.auth import require_auth, require_role, get_current_user
from utils.approval_codes import (
    generate_approval_code, hash_approval_code, verify_approval_code,
    is_code_expired, can_use_code
)
from models import to_dict

discount_approval_bp = Blueprint('discount_approval', __name__)

# Discount limits by role - Only owner can apply discounts
DISCOUNT_LIMITS = {
    'staff': 0,      # No discount access
    'manager': 0,   # No discount access
    'owner': 100     # Unlimited (only owner)
}

@discount_approval_bp.route('/', methods=['GET'])
@require_role('owner')
def list_approvals(current_user=None):
    """List discount approval requests - Owner only"""
    try:
        status = request.args.get('status', 'pending')
        requested_by_id = request.args.get('requested_by_id')
        
        query = Q(approval_status=status)
        
        # Only owners can see all requests
        if requested_by_id:
            query &= Q(requested_by=requested_by_id)
        
        approvals = DiscountApprovalRequest.objects(query).order_by('-created_at')
        
        result = []
        for approval in approvals:
            data = to_dict(approval)
            if approval.requested_by:
                data['requested_by_name'] = f"{approval.requested_by.first_name} {approval.requested_by.last_name or ''}".strip()
            if approval.approved_by:
                data['approved_by_name'] = f"{approval.approved_by.first_name} {approval.approved_by.last_name or ''}".strip()
            if approval.bill:
                data['bill_number'] = approval.bill.bill_number
            result.append(data)
        
        response = jsonify({'approvals': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>', methods=['GET'])
@require_role('owner')
def get_approval(approval_id, current_user=None):
    """Get a single approval request"""
    try:
        approval = DiscountApprovalRequest.objects(id=approval_id).first()
        if not approval:
            response = jsonify({'error': 'Approval request not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        result = to_dict(approval)
        if approval.bill:
            result['bill_details'] = {
                'bill_number': approval.bill.bill_number,
                'subtotal': approval.bill.subtotal,
                'final_amount': approval.bill.final_amount,
                'customer_name': f"{approval.bill.customer.first_name} {approval.bill.customer.last_name or ''}".strip() if approval.bill.customer else None
            }
        
        response = jsonify({'approval': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>/approve', methods=['POST'])
@require_role('owner')
def approve_request(approval_id, current_user=None):
    """Approve a discount request via in-app - Owner only"""
    try:
        approval = DiscountApprovalRequest.objects(id=approval_id).first()
        if not approval:
            response = jsonify({'error': 'Approval request not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        if approval.approval_status != 'pending':
            response = jsonify({'error': 'Approval request already processed'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Only owners can approve - no additional checks needed
        
        approval.approval_status = 'approved'
        approval.approval_method = 'in_app'
        approval.approved_at = datetime.utcnow()
        approval.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'approved'
            approval.bill.save()
        
        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount approved successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>/approve-with-code', methods=['POST'])
@require_role('owner')
def approve_with_code(approval_id, current_user=None):
    """Approve a discount request using an approval code"""
    try:
        approval = DiscountApprovalRequest.objects(id=approval_id).first()
        if not approval:
            response = jsonify({'error': 'Approval request not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        code = data.get('code')
        
        if not code:
            response = jsonify({'error': 'Approval code required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Find matching approval code
        approval_codes = ApprovalCode.objects(is_active=True)
        matched_code = None
        
        for approval_code in approval_codes:
            if verify_approval_code(code, approval_code.code_hash):
                # Check expiration
                if is_code_expired(approval_code.expires_at):
                    continue
                
                # Check usage limits
                if not can_use_code(approval_code.usage_count, approval_code.max_uses):
                    continue
                
                # Only owners can use approval codes
                user_role = current_user.get('role') if current_user else None
                if user_role != 'owner':
                    continue
                
                matched_code = approval_code
                break
        
        if not matched_code:
            response = jsonify({'error': 'Invalid or expired approval code'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Approve the request - only owners can approve
        
        approval.approval_status = 'approved'
        approval.approval_method = 'code'
        approval.approval_code_used = matched_code.code_hash
        approval.approved_at = datetime.utcnow()
        approval.save()
        
        # Update code usage
        matched_code.usage_count += 1
        matched_code.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'approved'
            approval.bill.save()
        
        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount approved with code'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>/reject', methods=['POST'])
@require_role('owner')
def reject_request(approval_id, current_user=None):
    """Reject a discount request"""
    try:
        approval = DiscountApprovalRequest.objects(id=approval_id).first()
        if not approval:
            response = jsonify({'error': 'Approval request not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        notes = data.get('notes', '')
        
        approval.approval_status = 'rejected'
        approval.notes = notes
        approval.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'rejected'
            approval.bill.save()
        
        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount request rejected'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Approval Code Routes (Owner only)
@discount_approval_bp.route('/approval-codes', methods=['POST'])
@require_role('owner')
def create_approval_code(current_user=None):
    """Generate a new approval code"""
    try:
        data = request.json
        role = data.get('role', 'manager')
        max_uses = data.get('max_uses')
        expires_in_days = data.get('expires_in_days')
        
        # Generate code
        code = generate_approval_code()
        code_hash = hash_approval_code(code)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Get creator
        manager = None
        if current_user and current_user.get('user_type') == 'manager':
            manager = Manager.objects(id=current_user['id']).first()
        
        approval_code = ApprovalCode(
            code_hash=code_hash,
            role=role,
            created_by=manager,
            max_uses=max_uses,
            expires_at=expires_at
        )
        approval_code.save()
        
        # Return the plain code (only shown once)
        response = jsonify({
            'code': code,  # Only returned on creation
            'id': str(approval_code.id),
            'role': role,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'max_uses': max_uses,
            'message': 'Save this code securely. It will not be shown again.'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/approval-codes', methods=['GET'])
@require_role('owner')
def list_approval_codes(current_user=None):
    """List all approval codes"""
    try:
        codes = ApprovalCode.objects().order_by('-created_at')
        result = []
        for code in codes:
            data = to_dict(code)
            # Don't expose the hash, just show status
            data['is_expired'] = is_code_expired(code.expires_at)
            data['can_use'] = can_use_code(code.usage_count, code.max_uses)
            del data['code_hash']  # Don't expose hash
            result.append(data)
        
        response = jsonify({'codes': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/approval-codes/<code_id>/deactivate', methods=['PUT'])
@require_role('owner')
def deactivate_code(code_id, current_user=None):
    """Deactivate an approval code"""
    try:
        code = ApprovalCode.objects(id=code_id).first()
        if not code:
            response = jsonify({'error': 'Approval code not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        code.is_active = False
        code.save()
        
        result = to_dict(code)
        response = jsonify({'code': result, 'message': 'Approval code deactivated'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

