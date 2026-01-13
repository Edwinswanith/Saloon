from flask import Blueprint, request, jsonify
from models import Staff, StaffTempAssignment
from datetime import datetime, date
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
@require_role('staff', 'manager', 'owner')
def get_staffs(current_user=None):
    """Get all staff members including temp-assigned staff"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        today = date.today()
        
        # Get permanent staff for this branch
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
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'first_name')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Apply sorting to permanent staff query
        if sort_by in ['first_name', 'last_name']:
            order_field = f"{sort_by},{'last_name' if sort_by == 'first_name' else 'first_name'}"
            if sort_order == 'desc':
                order_field = f"-{order_field}"
        else:
            order_field = f"-{sort_by}" if sort_order == 'desc' else sort_by
        
        permanent_staffs = list(query.order_by(order_field))
        
        # Get temp-assigned staff for this branch (currently active) - force evaluation
        temp_assigned_staffs = []
        if branch:
            temp_assignments = list(StaffTempAssignment.objects(
                temp_branch=branch,
                status='active',
                start_date__lte=today,
                end_date__gte=today
            ))
            for assignment in temp_assignments:
                temp_assigned_staffs.append({
                    'staff': assignment.staff,
                    'is_temp': True,
                    'original_branch': assignment.original_branch.name if assignment.original_branch else None,
                    'original_branch_id': str(assignment.original_branch.id) if assignment.original_branch else None,
                    'end_date': assignment.end_date.isoformat(),
                    'assignment_id': str(assignment.id)
                })
        
        # Build response
        staff_list = []
        
        # Add permanent staff
        for s in permanent_staffs:
            staff_list.append({
                'id': str(s.id),
                'mobile': s.mobile,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
                'salary': s.salary,
                'commissionRate': s.commission_rate,
                'branch': s.branch.name if s.branch else None,
                'branchId': str(s.branch.id) if s.branch else None,
                'isTemp': False,
                'originalBranch': None,
                'originalBranchId': None,
                'tempEndDate': None,
                'assignmentId': None
            })
        
        # Add temp-assigned staff
        for item in temp_assigned_staffs:
            s = item['staff']
            staff_list.append({
                'id': str(s.id),
                'mobile': s.mobile,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
                'salary': s.salary,
                'commissionRate': s.commission_rate,
                'isTemp': True,
                'originalBranch': item['original_branch'],
                'originalBranchId': item['original_branch_id'],
                'tempEndDate': item['end_date'],
                'assignmentId': item['assignment_id']
            })
        
        # Apply pagination to combined list
        total = len(staff_list)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_staff_list = staff_list[start_idx:end_idx]
        
        response = jsonify({
            'staffs': paginated_staff_list,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
            }
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

