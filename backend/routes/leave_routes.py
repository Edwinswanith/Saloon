from flask import Blueprint, request, jsonify
from models import StaffLeave, Staff, Branch, StaffTempAssignment
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_role, require_auth
from utils.branch_filter import get_selected_branch

leave_bp = Blueprint('leaves', __name__)

@leave_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@leave_bp.route('/', methods=['GET'])
@require_auth
def get_leaves(current_user=None):
    """Get all leave requests with optional filters"""
    try:
        branch_id = request.args.get('branch_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = StaffLeave.objects()
        
        # Filter by branch
        if branch_id and ObjectId.is_valid(branch_id):
            try:
                branch = Branch.objects.get(id=branch_id)
                query = query.filter(branch=branch)
            except DoesNotExist:
                pass
        
        # Filter by status
        if status:
            query = query.filter(status=status)
        
        # Filter by date range
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '')).date()
                query = query.filter(start_date__lte=start, end_date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '')).date()
                query = query.filter(start_date__lte=end, end_date__gte=end)
            except ValueError:
                pass
        
        leaves = query.order_by('-start_date')
        
        response = jsonify([{
            'id': str(l.id),
            'staff_id': str(l.staff.id),
            'staff_name': f"{l.staff.first_name} {l.staff.last_name}",
            'branch_id': str(l.branch.id) if l.branch else None,
            'branch_name': l.branch.name if l.branch else None,
            'start_date': l.start_date.isoformat() if l.start_date else None,
            'end_date': l.end_date.isoformat() if l.end_date else None,
            'leave_type': l.leave_type,
            'reason': l.reason,
            'status': l.status,
            'coverage_required': l.coverage_required,
            'covered_by_id': str(l.covered_by.id) if l.covered_by else None,
            'approved_by_id': str(l.approved_by.id) if l.approved_by else None,
            'rejection_reason': l.rejection_reason,
            'created_at': l.created_at.isoformat() if l.created_at else None
        } for l in leaves])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@leave_bp.route('/today', methods=['GET'])
@require_auth
def get_leaves_today(current_user=None):
    """Get all leaves active today"""
    try:
        today = date.today()
        
        leaves = StaffLeave.objects(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).order_by('branch', 'start_date')
        
        response = jsonify([{
            'id': str(l.id),
            'staff_id': str(l.staff.id),
            'staff_name': f"{l.staff.first_name} {l.staff.last_name}",
            'branch_id': str(l.branch.id) if l.branch else None,
            'branch_name': l.branch.name if l.branch else None,
            'start_date': l.start_date.isoformat() if l.start_date else None,
            'end_date': l.end_date.isoformat() if l.end_date else None,
            'leave_type': l.leave_type,
            'reason': l.reason,
            'coverage_required': l.coverage_required,
            'covered_by_id': str(l.covered_by.id) if l.covered_by else None,
            'covered': l.covered_by is not None
        } for l in leaves])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@leave_bp.route('/<id>', methods=['GET'])
@require_auth
def get_leave(id, current_user=None):
    """Get a single leave request"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid leave ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        l = StaffLeave.objects.get(id=id)
        
        response = jsonify({
            'id': str(l.id),
            'staff_id': str(l.staff.id),
            'staff_name': f"{l.staff.first_name} {l.staff.last_name}",
            'branch_id': str(l.branch.id) if l.branch else None,
            'branch_name': l.branch.name if l.branch else None,
            'start_date': l.start_date.isoformat() if l.start_date else None,
            'end_date': l.end_date.isoformat() if l.end_date else None,
            'leave_type': l.leave_type,
            'reason': l.reason,
            'status': l.status,
            'coverage_required': l.coverage_required,
            'covered_by_id': str(l.covered_by.id) if l.covered_by else None,
            'approved_by_id': str(l.approved_by.id) if l.approved_by else None,
            'rejection_reason': l.rejection_reason,
            'created_at': l.created_at.isoformat() if l.created_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Leave not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@leave_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_leave(current_user=None):
    """Create a new leave request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('staff_id') or not data.get('branch_id'):
            response = jsonify({'error': 'Staff and branch are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if not data.get('start_date') or not data.get('end_date'):
            response = jsonify({'error': 'Start and end dates are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate staff exists
        staff = Staff.objects.get(id=data['staff_id'])
        branch = Branch.objects.get(id=data['branch_id'])
        
        # Parse dates
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '')).date()
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '')).date()
        
        # Validate date range
        if end_date < start_date:
            response = jsonify({'error': 'End date must be after start date'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check for overlapping leaves
        from mongoengine import Q
        existing = StaffLeave.objects(
            staff=staff,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).first()
        
        if existing:
            response = jsonify({
                'error': f'Staff already has a leave from {existing.start_date} to {existing.end_date}'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Create leave
        leave = StaffLeave(
            staff=staff,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            leave_type=data.get('leave_type', 'casual'),
            reason=data.get('reason', ''),
            status=data.get('status', 'pending'),
            coverage_required=data.get('coverage_required', True)
        )
        leave.save()
        
        response = jsonify({
            'id': str(leave.id),
            'message': 'Leave request created successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except DoesNotExist:
        response = jsonify({'error': 'Staff or Branch not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except ValidationError as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@leave_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_leave(id, current_user=None):
    """Update a leave request (approve/reject/update)"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid leave ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        leave = StaffLeave.objects.get(id=id)
        data = request.get_json()
        
        # Update status
        if 'status' in data:
            if data['status'] in ['pending', 'approved', 'rejected', 'cancelled']:
                leave.status = data['status']
                if data['status'] == 'approved' and current_user:
                    leave.approved_by = current_user
                if data['status'] == 'rejected' and 'rejection_reason' in data:
                    leave.rejection_reason = data['rejection_reason']
        
        # Update dates if provided
        if 'start_date' in data:
            leave.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '')).date()
        
        if 'end_date' in data:
            leave.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '')).date()
        
        # Update other fields
        if 'leave_type' in data:
            leave.leave_type = data['leave_type']
        
        if 'reason' in data:
            leave.reason = data['reason']
        
        if 'coverage_required' in data:
            leave.coverage_required = data['coverage_required']
        
        # Link to temp assignment if provided
        if 'covered_by_id' in data and data['covered_by_id']:
            try:
                assignment = StaffTempAssignment.objects.get(id=data['covered_by_id'])
                leave.covered_by = assignment
            except DoesNotExist:
                pass
        
        leave.updated_at = datetime.utcnow()
        leave.save()
        
        response = jsonify({
            'id': str(leave.id),
            'message': 'Leave updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Leave not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@leave_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def cancel_leave(id, current_user=None):
    """Cancel a leave request"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid leave ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        leave = StaffLeave.objects.get(id=id)
        leave.status = 'cancelled'
        leave.updated_at = datetime.utcnow()
        leave.save()
        
        response = jsonify({
            'message': 'Leave cancelled successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Leave not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

