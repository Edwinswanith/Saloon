from flask import Blueprint, request, jsonify
from mongoengine import Q
from mongoengine.errors import DoesNotExist
from datetime import datetime, timedelta
from models import DiscountApprovalRequest, ApprovalCode, Bill, Staff, Manager, Owner, Notification
from utils.auth import require_auth, require_role, get_current_user
from utils.branch_filter import get_selected_branch
from utils.approval_codes import (
    generate_approval_code, hash_approval_code, verify_approval_code,
    is_code_expired, can_use_code
)
from models import to_dict

discount_approval_bp = Blueprint('discount_approval', __name__)

# Discount limits by role - staff cannot apply discounts; manager/owner can approve
DISCOUNT_LIMITS = {
    'staff': 0,      # No discount access
    'manager': 0,    # Can approve but not self-apply without approval
    'owner': 100     # Unlimited
}

@discount_approval_bp.route('/', methods=['GET'])
@require_role('owner', 'manager')
def list_approvals(current_user=None):
    """List discount approval requests - Owner and Manager"""
    try:
        status = request.args.get('status', 'pending')
        requested_by_id = request.args.get('requested_by_id')

        query = Q(approval_status=status)

        # Filter by branch
        branch = get_selected_branch(request, current_user)
        if branch:
            query &= (Q(branch=branch) | Q(branch=None))

        if requested_by_id:
            query &= Q(requested_by=requested_by_id)

        approvals = DiscountApprovalRequest.objects(query).order_by('-created_at')
        
        result = []
        for approval in approvals:
            try:
                data = to_dict(approval)
                
                # Get requested_by name — try Staff reference first, fall back to stored name
                data['requested_by_name'] = approval.requested_by_name or None
                data['requested_by_role'] = approval.requested_by_role or None
                if approval.requested_by:
                    try:
                        if hasattr(approval.requested_by, 'reload'):
                            approval.requested_by.reload()
                        if hasattr(approval.requested_by, 'first_name'):
                            data['requested_by_name'] = f"{approval.requested_by.first_name or ''} {approval.requested_by.last_name or ''}".strip() or data['requested_by_name']
                    except (DoesNotExist, AttributeError, Exception):
                        pass
                
                # Safely get approved_by name
                if approval.approved_by:
                    try:
                        if hasattr(approval.approved_by, 'reload'):
                            approval.approved_by.reload()
                        if hasattr(approval.approved_by, 'first_name'):
                            data['approved_by_name'] = f"{approval.approved_by.first_name or ''} {approval.approved_by.last_name or ''}".strip() or None
                    except (DoesNotExist, AttributeError, Exception):
                        data['approved_by_name'] = None
                
                # Safely get bill number
                if approval.bill:
                    try:
                        if hasattr(approval.bill, 'reload'):
                            approval.bill.reload()
                        data['bill_number'] = getattr(approval.bill, 'bill_number', None)
                    except (DoesNotExist, AttributeError, Exception):
                        data['bill_number'] = None
                
                result.append(data)
            except Exception as e:
                # Skip approval entries that can't be processed
                print(f"Error processing approval {approval.id}: {e}")
                continue
        
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
@require_role('owner', 'manager')
def approve_request(approval_id, current_user=None):
    """Approve a discount request via in-app - Owner and Manager"""
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
        
        # Record who approved
        if current_user:
            user_type = current_user.get('user_type', '')
            user_id = current_user.get('user_id') or current_user.get('id')
            if user_type == 'manager':
                approval.approved_by = Manager.objects(id=user_id).first()

        approval.approval_status = 'approved'
        approval.approval_method = 'in_app'
        approval.approved_at = datetime.utcnow()
        approval.updated_at = datetime.utcnow()
        approval.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'approved'
            approval.bill.save()

        # Resolve related notification
        Notification.objects(reference_id=str(approval.id), type='discount_approval').update(set__is_resolved=True)

        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount approved successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>/approve-with-code', methods=['POST'])
@require_role('owner', 'manager')
def approve_with_code(approval_id, current_user=None):
    """Approve a discount request using an approval code"""
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

        data = request.json
        code = data.get('code')

        if not code:
            response = jsonify({'error': 'Approval code required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Hash once and query directly instead of iterating all codes
        code_hash = hash_approval_code(code)
        matched_code = ApprovalCode.objects(code_hash=code_hash, is_active=True).first()

        if not matched_code:
            response = jsonify({'error': 'Invalid or expired approval code'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Validate expiration and usage
        if is_code_expired(matched_code.expires_at):
            response = jsonify({'error': 'Approval code has expired'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if not can_use_code(matched_code.usage_count, matched_code.max_uses):
            response = jsonify({'error': 'Approval code has reached its usage limit'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Record who approved
        if current_user:
            user_type = current_user.get('user_type', '')
            user_id = current_user.get('user_id') or current_user.get('id')
            if user_type == 'manager':
                approval.approved_by = Manager.objects(id=user_id).first()

        approval.approval_status = 'approved'
        approval.approval_method = 'code'
        approval.approval_code_used = matched_code.code_hash
        approval.approved_at = datetime.utcnow()
        approval.updated_at = datetime.utcnow()
        approval.save()
        
        # Update code usage
        matched_code.usage_count += 1
        matched_code.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'approved'
            approval.bill.save()

        Notification.objects(reference_id=str(approval.id), type='discount_approval').update(set__is_resolved=True)

        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount approved with code'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@discount_approval_bp.route('/<approval_id>/reject', methods=['POST'])
@require_role('owner', 'manager')
def reject_request(approval_id, current_user=None):
    """Reject a discount request"""
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

        data = request.json
        notes = data.get('notes', '')

        approval.approval_status = 'rejected'
        approval.notes = notes
        approval.updated_at = datetime.utcnow()
        approval.save()
        
        # Update bill
        if approval.bill:
            approval.bill.discount_approval_status = 'rejected'
            approval.bill.save()

        Notification.objects(reference_id=str(approval.id), type='discount_approval').update(set__is_resolved=True)

        result = to_dict(approval)
        response = jsonify({'approval': result, 'message': 'Discount request rejected'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Approval Code Routes (Owner and Manager can generate codes)
@discount_approval_bp.route('/approval-codes', methods=['POST'])
@require_role('owner', 'manager')
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
        
        # Get creator — handle both Manager and Owner
        # Note: created_by field only accepts Manager reference, so Owner references are stored as None
        creator_ref = None
        if current_user:
            user_type = current_user.get('user_type', '')
            user_id = current_user.get('user_id') or current_user.get('id')
            if user_type == 'manager':
                creator_ref = Manager.objects(id=user_id).first()
            # For owners, creator_ref remains None since ApprovalCode.created_by only accepts Manager references

        approval_code = ApprovalCode(
            code_hash=code_hash,
            role=role,
            created_by=creator_ref,
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
@require_role('owner', 'manager')
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
@require_role('owner', 'manager')
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

