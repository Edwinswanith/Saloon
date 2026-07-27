from flask import Blueprint, request, jsonify
from models import Staff, Branch
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth, require_role, hash_password

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
    """Get all staff members.

    All staff are visible across every branch — there is no per-branch filter.
    The Staff.branch field is retained as the staff's home branch (HR/payroll
    attribution) but does not restrict who appears in operational dropdowns.
    """
    try:
        query = Staff.objects()

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

        # Apply sorting
        if sort_by in ['first_name', 'last_name']:
            order_field = f"{sort_by},{'last_name' if sort_by == 'first_name' else 'first_name'}"
            if sort_order == 'desc':
                order_field = f"-{order_field}"
        else:
            order_field = f"-{sort_by}" if sort_order == 'desc' else sort_by

        all_staffs = list(query.order_by(order_field))

        staff_list = [{
            'id': str(s.id),
            'mobile': s.mobile,
            'firstName': s.first_name,
            'lastName': s.last_name,
            'email': s.email,
            'salary': s.salary,
            'commissionRate': s.commission_rate,
            'branch': s.branch.name if s.branch else None,
            'branchId': str(s.branch.id) if s.branch else None,
        } for s in all_staffs]

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
        
        # Get branch for assignment - check for explicit branch_id first
        branch = None
        branch_id = data.get('branch_id')
        if branch_id:
            try:
                if not ObjectId.is_valid(branch_id):
                    response = jsonify({'error': 'Invalid branch ID format'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
                branch = Branch.objects.get(id=branch_id)
            except DoesNotExist:
                response = jsonify({'error': 'Branch not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
        else:
            # Fall back to header-based branch selection
            branch = get_selected_branch(request, current_user)
        
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Mobile must be globally unique among ACTIVE staff. Staff are pooled
        # across all branches (no branch lock), so the same mobile in two
        # different branches would be ambiguous at login.
        if Staff.objects(mobile=data.get('mobile'), status='active').first():
            response = jsonify({'error': 'Staff with this mobile number already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate password
        password = data.get('password', '').strip()
        if not password:
            response = jsonify({'error': 'Password is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        if len(password) < 6:
            response = jsonify({'error': 'Password must be at least 6 characters'})
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
            branch=branch,
            password_hash=hash_password(password)
        )
        staff.save()

        response = jsonify({
            'id': str(staff.id),
            'message': 'Staff created successfully'
        })
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
        
        # Update mobile with global uniqueness check among ACTIVE staff
        # (excluding self). Staff are pooled across all branches.
        new_mobile = data.get('mobile')
        if new_mobile and new_mobile != staff.mobile:
            conflict = Staff.objects(
                mobile=new_mobile,
                status='active',
                id__ne=staff.id
            ).first()
            if conflict:
                response = jsonify({'error': 'Mobile number already in use'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            staff.mobile = new_mobile

        staff.first_name = data.get('firstName', staff.first_name)
        staff.last_name = data.get('lastName', staff.last_name)
        staff.email = data.get('email', staff.email)
        staff.salary = data.get('salary', staff.salary)
        staff.commission_rate = data.get('commissionRate', staff.commission_rate)
        staff.status = data.get('status', staff.status)

        # Optional password reset by manager/owner
        new_password = (data.get('password') or '').strip() if data.get('password') is not None else ''
        if new_password:
            if len(new_password) < 6:
                response = jsonify({'error': 'Password must be at least 6 characters'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            staff.password_hash = hash_password(new_password)
        
        # Update branch if branch_id is provided
        branch_id = data.get('branch_id')
        if branch_id:
            try:
                if not ObjectId.is_valid(branch_id):
                    response = jsonify({'error': 'Invalid branch ID format'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
                branch = Branch.objects.get(id=branch_id)
                staff.branch = branch
            except DoesNotExist:
                response = jsonify({'error': 'Branch not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
        
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
        # Also revoke login access so a deleted staff can't sign in
        staff.is_active = False
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


