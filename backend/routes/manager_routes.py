from flask import Blueprint, request, jsonify
from models import Manager
from datetime import datetime
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth, require_role
from mongoengine.errors import NotUniqueError, DoesNotExist

manager_bp = Blueprint('managers', __name__)

@manager_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@manager_bp.route('/', methods=['GET'])
@require_auth
def get_managers(current_user=None):
    """Get all managers"""
    try:
        status = request.args.get('status', 'all')
        role = request.args.get('role', 'manager')  # Default to manager, can be 'owner'
        
        # Start with basic query - don't fail if branch filtering fails
        query = Manager.objects(role=role)
        
        # Try to get branch for filtering, but don't fail if it doesn't work
        branch = None
        if current_user:
            try:
                branch = get_selected_branch(request, current_user)
            except Exception as e:
                # Log but don't fail - branch filtering is optional
                print(f"Warning: Could not get selected branch: {e}")
        
        # Filter by branch if specified (managers are assigned to branches)
        # Only filter by branch if we have a valid branch and role is manager
        if branch and role == 'manager':
            try:
                query = query.filter(branch=branch)
            except Exception as e:
                print(f"Warning: Could not filter by branch: {e}")
                # Continue without branch filter
        
        if status != 'all':
            query = query.filter(status=status)
        
        # Execute query and convert to list
        managers = list(query.order_by('-created_at'))
        
        # Build response - handle missing fields gracefully
        managers_list = []
        for m in managers:
            try:
                managers_list.append({
                    'id': str(m.id),
                    'name': f"{getattr(m, 'first_name', '')} {getattr(m, 'last_name', '') or ''}".strip(),
                    'firstName': getattr(m, 'first_name', ''),
                    'lastName': getattr(m, 'last_name', '') or '',
                    'email': getattr(m, 'email', ''),
                    'mobile': getattr(m, 'mobile', ''),
                    'salon': getattr(m, 'salon', '') or '',
                    'status': getattr(m, 'status', 'active'),
                    'role': getattr(m, 'role', 'manager')
                })
            except Exception as e:
                print(f"Warning: Failed to serialize manager {getattr(m, 'id', 'unknown')}: {e}")
                # Skip this manager but continue
                continue
        
        response = jsonify({
            'managers': managers_list
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"ERROR in get_managers: {error_msg}")
        traceback.print_exc()
        response = jsonify({'error': error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@manager_bp.route('/<manager_id>', methods=['GET'])
@require_auth
def get_manager(manager_id, current_user=None):
    """Get single manager"""
    try:
        if not ObjectId.is_valid(manager_id):
            response = jsonify({'error': 'Invalid manager ID format'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        manager = Manager.objects(id=manager_id).first()
        if not manager:
            response = jsonify({'error': 'Manager not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        response = jsonify({
            'id': str(manager.id),
            'firstName': manager.first_name,
            'lastName': manager.last_name or '',
            'email': manager.email,
            'mobile': manager.mobile,
            'salon': manager.salon or '',
            'status': manager.status,
            'role': manager.role
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@manager_bp.route('/', methods=['POST'])
@require_role('owner')
def create_manager(current_user=None):
    """Create new manager"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('firstName'):
            response = jsonify({'error': 'First name is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        if not data.get('email'):
            response = jsonify({'error': 'Email is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        if not data.get('mobile'):
            response = jsonify({'error': 'Mobile is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check if email already exists
        if Manager.objects(email=data.get('email')).first():
            response = jsonify({'error': 'Manager with this email already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check if mobile already exists
        if Manager.objects(mobile=data.get('mobile')).first():
            response = jsonify({'error': 'Manager with this mobile number already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Get branch for assignment
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        manager = Manager(
            first_name=data.get('firstName'),
            last_name=data.get('lastName', ''),
            email=data.get('email'),
            mobile=data.get('mobile'),
            salon=data.get('salon', ''),
            role=data.get('role', 'manager'),
            status=data.get('status', 'active'),
            branch=branch
        )
        
        # Hash password if provided
        if data.get('password'):
            from utils.auth import hash_password
            manager.password_hash = hash_password(data.get('password'))
        
        manager.save()
        
        response = jsonify({
            'id': str(manager.id),
            'message': 'Manager created successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except NotUniqueError:
        response = jsonify({'error': 'Manager with this email or mobile already exists'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@manager_bp.route('/<manager_id>', methods=['PUT'])
@require_role('owner')
def update_manager(manager_id, current_user=None):
    """Update manager"""
    try:
        if not ObjectId.is_valid(manager_id):
            response = jsonify({'error': 'Invalid manager ID format'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        manager = Manager.objects(id=manager_id).first()
        if not manager:
            response = jsonify({'error': 'Manager not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.get_json()
        
        if 'firstName' in data:
            manager.first_name = data['firstName']
        if 'lastName' in data:
            manager.last_name = data.get('lastName', '')
        if 'email' in data:
            # Check if email is being changed and if it already exists
            if data['email'] != manager.email:
                if Manager.objects(email=data['email']).first():
                    response = jsonify({'error': 'Manager with this email already exists'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
            manager.email = data['email']
        if 'mobile' in data:
            # Check if mobile is being changed and if it already exists
            if data['mobile'] != manager.mobile:
                if Manager.objects(mobile=data['mobile']).first():
                    response = jsonify({'error': 'Manager with this mobile number already exists'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
            manager.mobile = data['mobile']
        if 'salon' in data:
            manager.salon = data['salon']
        if 'status' in data:
            manager.status = data['status']
        if 'password' in data and data['password']:
            from utils.auth import hash_password
            manager.password_hash = hash_password(data['password'])
        
        manager.updated_at = datetime.utcnow()
        manager.save()
        
        response = jsonify({'message': 'Manager updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except NotUniqueError:
        response = jsonify({'error': 'Manager with this email or mobile already exists'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@manager_bp.route('/<manager_id>', methods=['DELETE'])
@require_role('owner')
def delete_manager(manager_id, current_user=None):
    """Delete manager (soft delete by setting status to inactive)"""
    try:
        if not ObjectId.is_valid(manager_id):
            response = jsonify({'error': 'Invalid manager ID format'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        manager = Manager.objects(id=manager_id).first()
        if not manager:
            response = jsonify({'error': 'Manager not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        manager.status = 'inactive'
        manager.is_active = False
        manager.updated_at = datetime.utcnow()
        manager.save()
        
        response = jsonify({'message': 'Manager deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
