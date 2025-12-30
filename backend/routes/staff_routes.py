from flask import Blueprint, request, jsonify
from models import Staff
from datetime import datetime
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth, require_role

staff_bp = Blueprint('staffs', __name__)

@staff_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@staff_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_staffs(current_user=None):
    """Get all staff members (Manager and Owner only)"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Staff.objects()
        if branch:
            query = query.filter(branch=branch)
        # Filter by active status if specified, otherwise show all
        status_filter = request.args.get('status')
        if status_filter:
            query = query.filter(status=status_filter)
        else:
            # Default: show active staff, but also include staff without status set
            from mongoengine import Q
            query = query.filter(Q(status='active') | Q(status__exists=False))
        
        staffs = query.order_by('first_name', 'last_name')
        
        response = jsonify({
            'staffs': [{
                'id': str(s.id),
                'mobile': s.mobile,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
                'salary': s.salary,
                'commissionRate': s.commission_rate
            } for s in staffs]
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['GET'])
@require_role('manager', 'owner')
def get_staff(staff_id, current_user=None):
    """Get single staff member (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        response = jsonify({
            'id': str(staff.id),
            'mobile': staff.mobile,
            'firstName': staff.first_name,
            'lastName': staff.last_name,
            'email': staff.email,
            'salary': staff.salary,
            'commissionRate': staff.commission_rate,
            'status': staff.status
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_staff(current_user=None):
    """Create new staff member (Manager and Owner only)"""
    try:
        data = request.get_json()
        
        # Get branch for assignment
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if Staff.objects(mobile=data.get('mobile')).first():
            response = jsonify({'error': 'Staff with this mobile number already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        staff = Staff(
            mobile=data.get('mobile'),
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('email', ''),
            salary=data.get('salary'),
            commission_rate=data.get('commissionRate', 0.0),
            status=data.get('status', 'active'),
            branch=branch
        )
        staff.save()
        
        response = jsonify({'id': str(staff.id), 'message': 'Staff created successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except NotUniqueError:
        response = jsonify({'error': 'Staff with this mobile number already exists'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_staff(staff_id, current_user=None):
    """Update staff member (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        data = request.get_json()
        
        staff.first_name = data.get('firstName', staff.first_name)
        staff.last_name = data.get('lastName', staff.last_name)
        staff.email = data.get('email', staff.email)
        staff.salary = data.get('salary', staff.salary)
        staff.commission_rate = data.get('commissionRate', staff.commission_rate)
        staff.status = data.get('status', staff.status)
        staff.updated_at = datetime.utcnow()
        staff.save()
        
        response = jsonify({'message': 'Staff updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_staff(staff_id, current_user=None):
    """Delete staff member (Manager and Owner only - soft delete by setting status to inactive)"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        staff.status = 'inactive'
        staff.updated_at = datetime.utcnow()
        staff.save()
        response = jsonify({'message': 'Staff deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

