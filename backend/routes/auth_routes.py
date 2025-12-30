"""
Authentication routes for login, logout, and user management
"""
from flask import Blueprint, request, jsonify
from models import Staff, Manager, Owner, LoginHistory, Branch
from utils.auth import (
    hash_password,
    verify_password,
    generate_jwt_token,
    require_auth,
    get_current_user
)
from datetime import datetime
from bson import ObjectId
import os

auth_bp = Blueprint('auth', __name__)

# Password functionality removed for managers and owners - they can log in without password


@auth_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - supports both staff and manager login

    Request body:
    {
        "user_type": "staff" or "manager",
        "identifier": "mobile or email",
        "role": "staff" (optional for staff without password),
        "password": "password" (not used for manager/owner - password functionality removed),
        "branch_id": "branch_id" (optional, validates user access to branch)
    }

    Returns:
    {
        "token": "JWT token",
        "user": {user details},
        "role": "staff|manager|owner",
        "branch": {selected branch info}
    }
    """
    try:
        data = request.get_json()

        if not data:
            response = jsonify({'error': 'Request body is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        user_type = data.get('user_type', 'staff')  # Default to staff
        identifier = data.get('identifier', '').strip()  # Mobile or email
        password = data.get('password', '').strip()
        role = data.get('role', 'staff').strip()  # For staff without password
        branch_id = data.get('branch_id', '').strip()  # Selected branch ID

        if not identifier:
            response = jsonify({'error': 'Mobile number or email is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Handle Staff login
        if user_type == 'staff':
            # Find staff by mobile - handle missing is_active field
            staff = Staff.objects(mobile=identifier).first()

            if not staff:
                # Log failed login attempt
                try:
                    LoginHistory(
                        user_id=identifier,
                        user_type='staff',
                        role='unknown',
                        login_method='password',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        login_status='failed',
                        failure_reason='Staff member not found'
                    ).save()
                except:
                    pass  # Don't fail if login history fails
                
                response = jsonify({'error': 'Staff member not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            # Check if explicitly inactive (treat None/missing as active)
            is_active = staff.is_active if staff.is_active is not None else True
            if is_active is False:
                try:
                    LoginHistory(
                        user_id=str(staff.id),
                        user_type='staff',
                        role=staff.role or 'staff',
                        login_method='password',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        login_status='failed',
                        failure_reason='Staff account is inactive'
                    ).save()
                except:
                    pass
                
                response = jsonify({'error': 'Staff account is inactive'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 403

            # If staff has a password set (manager/owner role), verify it
            if staff.password_hash:
                if not password:
                    try:
                        LoginHistory(
                            user_id=str(staff.id),
                            user_type='staff',
                            role=staff.role,
                            login_method='password',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', ''),
                            login_status='failed',
                            failure_reason='Password required but not provided'
                        ).save()
                    except:
                        pass
                    response = jsonify({'error': 'Password is required for this user'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400

                if not verify_password(password, staff.password_hash):
                    try:
                        LoginHistory(
                            user_id=str(staff.id),
                            user_type='staff',
                            role=staff.role,
                            login_method='password',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', ''),
                            login_status='failed',
                            failure_reason='Invalid password'
                        ).save()
                    except:
                        pass
                    response = jsonify({'error': 'Invalid password'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 401
            else:
                # Staff without password - use role selection
                # Update staff role if provided
                if role in ['staff', 'manager', 'owner']:
                    staff.role = role
                    staff.save()

            # Generate JWT token
            full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
            token = generate_jwt_token(
                user_id=str(staff.id),
                role=staff.role,
                user_type='staff',
                name=full_name
            )

            # Validate and set selected branch
            selected_branch = None
            if branch_id:
                # Validate branch_id format
                if not ObjectId.is_valid(branch_id):
                    response = jsonify({'error': 'Invalid branch ID format'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
                
                # Get branch
                branch = Branch.objects(id=branch_id).first()
                if not branch:
                    response = jsonify({'error': 'Branch not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404
                
                # Staff can only access their assigned branch
                if staff.branch and str(staff.branch.id) != branch_id:
                    response = jsonify({'error': 'You do not have access to this branch'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 403
                
                selected_branch = branch
            else:
                # Use staff's assigned branch if no branch_id provided
                selected_branch = staff.branch

            # Log login history
            try:
                login_method = 'password' if staff.password_hash else 'role_selection'
                LoginHistory(
                    user_id=str(staff.id),
                    user_type='staff',
                    role=staff.role,
                    login_method=login_method,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    login_status='success'
                ).save()
            except Exception as e:
                print(f"Failed to log login history: {e}")

            # Get branch info
            branch_info = None
            if selected_branch:
                branch_info = {
                    'id': str(selected_branch.id),
                    'name': selected_branch.name,
                    'city': selected_branch.city
                }
            
            response = jsonify({
                'token': token,
                'user': {
                    'id': str(staff.id),
                    'mobile': staff.mobile,
                    'first_name': staff.first_name,
                    'last_name': staff.last_name,
                    'email': staff.email,
                    'role': staff.role,
                    'user_type': 'staff',
                    'branch_id': str(selected_branch.id) if selected_branch else None,
                    'branch': branch_info
                },
                'role': staff.role,
                'branch_id': str(selected_branch.id) if selected_branch else None,
                'branch': branch_info,
                'message': 'Login successful'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        # Handle Manager/Owner login
        elif user_type == 'manager':
            # Check if this is an owner login (role='owner' in request)
            requested_role = request.get_json().get('role', 'manager')
            
            if requested_role == 'owner':
                # Handle Owner login - check Owner collection
                from mongoengine import Q
                owner = Owner.objects(
                    (Owner.email == identifier) | (Owner.mobile == identifier)
                ).first()

                if not owner:
                    # Log failed login attempt
                    try:
                        LoginHistory(
                            user_id=identifier,
                            user_type='manager',
                            role='owner',
                            login_method='password',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', ''),
                            login_status='failed',
                            failure_reason='Owner not found'
                        ).save()
                    except:
                        pass
                    response = jsonify({'error': 'Owner not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404
                
                # Check if explicitly inactive
                is_active = owner.is_active if owner.is_active is not None else True
                if is_active is False:
                    try:
                        LoginHistory(
                            user_id=str(owner.id),
                            user_type='manager',
                            role='owner',
                            login_method='password',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', ''),
                            login_status='failed',
                            failure_reason='Owner account is inactive'
                        ).save()
                    except:
                        pass
                    response = jsonify({'error': 'Owner account is inactive'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 403

                # Password functionality removed - owners can log in without password
                # Generate JWT token
                full_name = f"{owner.first_name} {owner.last_name or ''}".strip()
                token = generate_jwt_token(
                    user_id=str(owner.id),
                    role='owner',
                    user_type='manager',
                    name=full_name
                )

                # Validate and set selected branch (Owner can access any branch)
                selected_branch = None
                if branch_id:
                    # Validate branch_id format
                    if not ObjectId.is_valid(branch_id):
                        response = jsonify({'error': 'Invalid branch ID format'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400
                    
                    # Get branch
                    branch = Branch.objects(id=branch_id).first()
                    if not branch:
                        response = jsonify({'error': 'Branch not found'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 404
                    
                    selected_branch = branch

                # Log login history
                try:
                    LoginHistory(
                        user_id=str(owner.id),
                        user_type='manager',
                        role='owner',
                        login_method='password',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        login_status='success'
                    ).save()
                except Exception as e:
                    print(f"Failed to log login history: {e}")

                # Get branch info
                branch_info = None
                if selected_branch:
                    branch_info = {
                        'id': str(selected_branch.id),
                        'name': selected_branch.name,
                        'city': selected_branch.city
                    }

                # Owner doesn't have a branch - has access to all branches
                response = jsonify({
                    'token': token,
                    'user': {
                        'id': str(owner.id),
                        'mobile': owner.mobile,
                        'email': owner.email,
                        'first_name': owner.first_name,
                        'last_name': owner.last_name,
                        'role': 'owner',
                        'salon': owner.salon,
                        'user_type': 'manager',
                        'branch_id': str(selected_branch.id) if selected_branch else None,
                        'branch': branch_info
                    },
                    'role': 'owner',
                    'branch_id': str(selected_branch.id) if selected_branch else None,
                    'branch': branch_info,
                    'message': 'Login successful'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 200
            
            # Handle Manager login - check Manager collection
            # Find manager by email or mobile - filter by branch to ensure correct manager
            from mongoengine import Q
            
            # Build query: find by email/mobile
            query = Manager.objects(
                (Manager.email == identifier) | (Manager.mobile == identifier)
            )
            
            # If branch_id provided, filter by branch to avoid loading wrong manager
            if branch_id and ObjectId.is_valid(branch_id):
                branch_obj = Branch.objects(id=branch_id).first()
                if branch_obj:
                    query = query.filter(branch=branch_obj.id)
                    print(f"DEBUG: Manager login - filtering by branch: {branch_obj.name} (ID: {branch_id})")
            
            manager = query.first()

            if not manager:
                # Log failed login attempt
                try:
                    LoginHistory(
                        user_id=identifier,
                        user_type='manager',
                        role='unknown',
                        login_method='password',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        login_status='failed',
                        failure_reason='Manager not found'
                    ).save()
                except:
                    pass
                response = jsonify({'error': 'Manager not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            # Check if explicitly inactive (treat None/missing as active)
            is_active = manager.is_active if manager.is_active is not None else True
            if is_active is False:
                try:
                    LoginHistory(
                        user_id=str(manager.id),
                        user_type='manager',
                        role=manager.role or 'manager',
                        login_method='password',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        login_status='failed',
                        failure_reason='Manager account is inactive'
                    ).save()
                except:
                    pass
                response = jsonify({'error': 'Manager account is inactive'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 403

            # Password functionality removed - managers can log in without password
            # Generate JWT token

            # Generate JWT token
            full_name = f"{manager.first_name} {manager.last_name or ''}".strip()
            token = generate_jwt_token(
                user_id=str(manager.id),
                role=manager.role,
                user_type='manager',
                name=full_name
            )

            # Validate and set selected branch
            selected_branch = None
            if branch_id:
                # Validate branch_id format
                if not ObjectId.is_valid(branch_id):
                    response = jsonify({'error': 'Invalid branch ID format'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
                
                # Get branch
                branch = Branch.objects(id=branch_id).first()
                if not branch:
                    response = jsonify({'error': 'Branch not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404
                
                # Manager can only access their assigned branch, Owner can access any branch
                if manager.role != 'owner':
                    # Check if manager has a branch assigned
                    if not manager.branch:
                        response = jsonify({'error': 'No branch assigned to this manager. Please contact administrator.'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 403

                    # Normalize both IDs to strings for comparison
                    manager_branch_id = str(manager.branch.id)
                    selected_branch_id = str(branch_id)

                    # Add debug logging
                    print(f"DEBUG: Manager branch validation:")
                    print(f"  Manager: {manager.first_name} {manager.last_name}")
                    print(f"  Manager's branch ID: {manager_branch_id}")
                    print(f"  Manager's branch name: {manager.branch.name}")
                    print(f"  Selected branch ID: {selected_branch_id}")
                    print(f"  Match: {manager_branch_id == selected_branch_id}")

                    # Use same validation logic as staff login
                    if manager_branch_id != selected_branch_id:
                        # Manager selected wrong branch - reject login
                        branch_name = manager.branch.name if manager.branch else 'Unknown'
                        response = jsonify({
                            'error': f'You are assigned to branch: {branch_name}. Please select that branch to log in.',
                            'assigned_branch_id': manager_branch_id,
                            'assigned_branch_name': branch_name
                        })
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 403

                    # Correct branch selected - manager's branch matches selected branch
                    selected_branch = branch
                else:
                    # Owner can access any branch
                    selected_branch = branch
            else:
                # Use manager's assigned branch if no branch_id provided (Owner may not have branch)
                selected_branch = manager.branch

            # Log login history
            try:
                LoginHistory(
                    user_id=str(manager.id),
                    user_type='manager',
                    role=manager.role,
                    login_method='password',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    login_status='success'
                ).save()
            except Exception as e:
                print(f"Failed to log login history: {e}")

            # Get branch info
            branch_info = None
            if selected_branch:
                branch_info = {
                    'id': str(selected_branch.id),
                    'name': selected_branch.name,
                    'city': selected_branch.city
                }
            
            response = jsonify({
                'token': token,
                'user': {
                    'id': str(manager.id),
                    'mobile': manager.mobile,
                    'email': manager.email,
                    'first_name': manager.first_name,
                    'last_name': manager.last_name,
                    'role': manager.role,
                    'salon': manager.salon,
                    'user_type': 'manager',
                    'branch_id': str(selected_branch.id) if selected_branch else None,
                    'branch': branch_info
                },
                'role': manager.role,
                'branch_id': str(selected_branch.id) if selected_branch else None,
                'branch': branch_info,
                'message': 'Login successful'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        else:
            response = jsonify({'error': 'Invalid user_type. Must be "staff" or "manager"'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Login failed', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout(current_user=None):
    """
    Logout endpoint (mainly for logging purposes, token invalidation handled client-side)
    Works for staff, manager, and owner - same behavior for all user types
    """
    response = jsonify({'message': 'Logout successful'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response, 200


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_info(current_user=None):
    """
    Get current authenticated user information
    """
    try:
        if not current_user:
            return jsonify({'error': 'Not authenticated'}), 401

        user_type = current_user.get('user_type')
        user_id = current_user.get('user_id')

        if user_type == 'staff':
            staff = Staff.objects(id=user_id).first()
            if not staff:
                response = jsonify({'error': 'User not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404

            response = jsonify({
                'user': {
                    'id': str(staff.id),
                    'mobile': staff.mobile,
                    'first_name': staff.first_name,
                    'last_name': staff.last_name,
                    'email': staff.email,
                    'role': staff.role,
                    'user_type': 'staff',
                    'status': staff.status
                }
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        elif user_type == 'manager':
            # Check if user is owner (role='owner' in token)
            user_role = current_user.get('role')
            if user_role == 'owner':
                owner = Owner.objects(id=user_id).first()
                if not owner:
                    response = jsonify({'error': 'User not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404

                response = jsonify({
                    'user': {
                        'id': str(owner.id),
                        'mobile': owner.mobile,
                        'email': owner.email,
                        'first_name': owner.first_name,
                        'last_name': owner.last_name,
                        'role': 'owner',
                        'salon': owner.salon,
                        'user_type': 'manager',
                        'status': owner.status
                    }
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 200
            else:
                manager = Manager.objects(id=user_id).first()
                if not manager:
                    response = jsonify({'error': 'User not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404

                response = jsonify({
                    'user': {
                        'id': str(manager.id),
                        'mobile': manager.mobile,
                        'email': manager.email,
                        'first_name': manager.first_name,
                        'last_name': manager.last_name,
                        'role': manager.role,
                        'salon': manager.salon,
                        'user_type': 'manager',
                        'status': manager.status
                    }
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 200

        response = jsonify({'error': 'Invalid user type'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400

    except Exception as e:
        print(f"Get user info error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Failed to get user info', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile(current_user=None):
    """
    Update current user's profile information
    
    Request body:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "mobile": "9876543210" (for staff only)
    }
    """
    try:
        if not current_user:
            response = jsonify({'error': 'Not authenticated'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 401

        data = request.get_json()
        if not data:
            response = jsonify({'error': 'Request body is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        user_type = current_user.get('user_type')
        user_id = current_user.get('user_id')

        if user_type == 'staff':
            staff = Staff.objects(id=user_id).first()
            if not staff:
                response = jsonify({'error': 'User not found'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404

            # Update allowed fields
            if 'first_name' in data:
                staff.first_name = data['first_name']
            if 'last_name' in data:
                staff.last_name = data.get('last_name', '')
            if 'email' in data:
                staff.email = data['email']
            if 'mobile' in data:
                # Check if mobile is already taken by another staff
                existing = Staff.objects(mobile=data['mobile']).first()
                if existing and str(existing.id) != user_id:
                    response = jsonify({'error': 'Mobile number already in use'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 400
                staff.mobile = data['mobile']

            staff.updated_at = datetime.utcnow()
            staff.save()

            response = jsonify({
                'message': 'Profile updated successfully',
                'user': {
                    'id': str(staff.id),
                    'mobile': staff.mobile,
                    'first_name': staff.first_name,
                    'last_name': staff.last_name,
                    'email': staff.email,
                    'role': staff.role,
                    'user_type': 'staff',
                    'status': staff.status
                }
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        elif user_type == 'manager':
            # Check if user is owner
            user_role = current_user.get('role')
            if user_role == 'owner':
                owner = Owner.objects(id=user_id).first()
                if not owner:
                    response = jsonify({'error': 'User not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404

                # Update allowed fields
                if 'first_name' in data:
                    owner.first_name = data['first_name']
                if 'last_name' in data:
                    owner.last_name = data.get('last_name', '')
                if 'email' in data:
                    # Check if email is already taken by another owner
                    existing = Owner.objects(email=data['email']).first()
                    if existing and str(existing.id) != user_id:
                        response = jsonify({'error': 'Email already in use'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400
                    owner.email = data['email']
                if 'mobile' in data:
                    # Check if mobile is already taken by another owner
                    existing = Owner.objects(mobile=data['mobile']).first()
                    if existing and str(existing.id) != user_id:
                        response = jsonify({'error': 'Mobile number already in use'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400
                    owner.mobile = data['mobile']
                if 'salon' in data:
                    owner.salon = data['salon']

                owner.updated_at = datetime.utcnow()
                owner.save()

                response = jsonify({
                    'message': 'Profile updated successfully',
                    'user': {
                        'id': str(owner.id),
                        'mobile': owner.mobile,
                        'email': owner.email,
                        'first_name': owner.first_name,
                        'last_name': owner.last_name,
                        'role': 'owner',
                        'salon': owner.salon,
                        'user_type': 'manager',
                        'status': owner.status
                    }
                })
            else:
                manager = Manager.objects(id=user_id).first()
                if not manager:
                    response = jsonify({'error': 'User not found'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 404

                # Update allowed fields
                if 'first_name' in data:
                    manager.first_name = data['first_name']
                if 'last_name' in data:
                    manager.last_name = data.get('last_name', '')
                if 'email' in data:
                    # Check if email is already taken by another manager
                    existing = Manager.objects(email=data['email']).first()
                    if existing and str(existing.id) != user_id:
                        response = jsonify({'error': 'Email already in use'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400
                    manager.email = data['email']
                if 'mobile' in data:
                    # Check if mobile is already taken by another manager
                    existing = Manager.objects(mobile=data['mobile']).first()
                    if existing and str(existing.id) != user_id:
                        response = jsonify({'error': 'Mobile number already in use'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400
                    manager.mobile = data['mobile']
                if 'salon' in data:
                    manager.salon = data['salon']

                manager.updated_at = datetime.utcnow()
                manager.save()

                response = jsonify({
                    'message': 'Profile updated successfully',
                    'user': {
                        'id': str(manager.id),
                        'mobile': manager.mobile,
                        'email': manager.email,
                        'first_name': manager.first_name,
                        'last_name': manager.last_name,
                        'role': manager.role,
                        'salon': manager.salon,
                        'user_type': 'manager',
                        'status': manager.status
                    }
                })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        response = jsonify({'error': 'Invalid user type'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400

    except Exception as e:
        print(f"Update profile error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Failed to update profile', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/change-password', methods=['PUT'])
@require_auth
def change_password(current_user=None):
    """
    Change password for current user

    Request body:
    {
        "old_password": "current password",
        "new_password": "new password"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()

        if not old_password or not new_password:
            return jsonify({'error': 'Both old and new passwords are required'}), 400

        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400

        user_type = current_user.get('user_type')
        user_id = current_user.get('user_id')

        if user_type == 'staff':
            staff = Staff.objects(id=user_id).first()
            if not staff:
                return jsonify({'error': 'User not found'}), 404

            # Verify old password if set
            if staff.password_hash:
                if not verify_password(old_password, staff.password_hash):
                    return jsonify({'error': 'Current password is incorrect'}), 401

            # Set new password
            staff.password_hash = hash_password(new_password)
            staff.updated_at = datetime.utcnow()
            staff.save()

            return jsonify({'message': 'Password changed successfully'}), 200

        elif user_type == 'manager':
            # Check if user is owner
            user_role = current_user.get('role')
            if user_role == 'owner':
                owner = Owner.objects(id=user_id).first()
                if not owner:
                    return jsonify({'error': 'User not found'}), 404

                # Verify old password
                if not owner.password_hash:
                    return jsonify({'error': 'Password not set for this account'}), 400

                if not verify_password(old_password, owner.password_hash):
                    return jsonify({'error': 'Current password is incorrect'}), 401

                # Set new password
                owner.password_hash = hash_password(new_password)
                owner.updated_at = datetime.utcnow()
                owner.save()

                return jsonify({'message': 'Password changed successfully'}), 200
            else:
                manager = Manager.objects(id=user_id).first()
                if not manager:
                    return jsonify({'error': 'User not found'}), 404

                # Verify old password
                if not manager.password_hash:
                    return jsonify({'error': 'Password not set for this account'}), 400

                if not verify_password(old_password, manager.password_hash):
                    return jsonify({'error': 'Current password is incorrect'}), 401

                # Set new password
                manager.password_hash = hash_password(new_password)
                manager.updated_at = datetime.utcnow()
                manager.save()

                return jsonify({'message': 'Password changed successfully'}), 200

        return jsonify({'error': 'Invalid user type'}), 400

    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'error': 'Failed to change password', 'message': str(e)}), 500


@auth_bp.route('/set-password', methods=['POST'])
def set_initial_password():
    """
    Set initial password for manager (development only - should be secured in production)

    Request body:
    {
        "email": "manager@example.com",
        "password": "password"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        manager = Manager.objects(email=email).first()

        if not manager:
            return jsonify({'error': 'Manager not found'}), 404

        # Hash and set password
        manager.password_hash = hash_password(password)
        manager.updated_at = datetime.utcnow()
        manager.save()

        return jsonify({
            'message': 'Password set successfully',
            'email': email
        }), 200

    except Exception as e:
        print(f"Set password error: {e}")
        return jsonify({'error': 'Failed to set password', 'message': str(e)}), 500


@auth_bp.route('/staff-list', methods=['GET'])
def get_staff_list():
    """
    Get list of staff members for login selection (public endpoint for login screen)
    Optional query parameter: branch_id - filter by branch
    """
    try:
        from mongoengine import Q
        from models import Branch
        from bson import ObjectId
        
        # Get branch_id from query parameter
        branch_id = request.args.get('branch_id')
        branch = None
        if branch_id and ObjectId.is_valid(branch_id):
            branch = Branch.objects(id=branch_id).first()
        
        # Get all staff members first, then filter in Python
        # This handles cases where fields might be missing or None
        query = Staff.objects()
        if branch:
            query = query.filter(branch=branch)
        
        all_staff = query.only(
            'id', 'mobile', 'first_name', 'last_name', 'role', 'is_active', 'status', 'branch'
        )

        staff_list = []
        for staff in all_staff:
            # Skip only if explicitly marked as inactive
            # Handle None/missing values as active (default behavior)
            is_active = staff.is_active if staff.is_active is not None else True
            status = staff.status if staff.status else 'active'
            
            if is_active is False:
                continue
            if status == 'inactive':
                continue
                
            staff_list.append({
                'id': str(staff.id),
                'mobile': staff.mobile,
                'name': f"{staff.first_name} {staff.last_name or ''}".strip(),
                'role': staff.role or 'staff',
                'branch_id': str(staff.branch.id) if staff.branch else None,
                'branch_name': staff.branch.name if staff.branch else None
            })

        response = jsonify({
            'staff': staff_list,
            'count': len(staff_list),
            'branch_id': branch_id,
            'branch_name': branch.name if branch else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        
        print(f"Returning {len(staff_list)} staff members for login (branch: {branch.name if branch else 'All'})")
        return response, 200

    except Exception as e:
        print(f"Get staff list error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({
            'error': 'Failed to get staff list',
            'message': str(e),
            'staff': []  # Return empty array on error
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/manager-list', methods=['GET'])
def get_manager_list():
    """
    Get list of managers/owners for login selection (public endpoint for login screen)
    Optional query parameters:
    - role: filter by role ('manager' or 'owner')
    - branch_id: filter by branch (for managers only, owners are shown for all branches)
    """
    try:
        from models import Branch
        from bson import ObjectId
        
        # Get filters from query parameters - ensure branch_id is always defined
        role_filter = request.args.get('role')  # 'manager' or 'owner'
        branch_id = request.args.get('branch_id') or None  # Explicitly set to None if not provided
        
        # Get branch if branch_id is provided
        branch = None
        if branch_id and ObjectId.is_valid(branch_id):
            branch = Branch.objects(id=branch_id).first()
            if branch:
                print(f"DEBUG: Filtering managers by branch: {branch.name}")
            else:
                print(f"DEBUG: Invalid branch_id: {branch_id}")
        
        manager_list = []
        
        # If role filter is 'owner', query Owner collection
        if role_filter == 'owner':
            owners = Owner.objects()
            print(f"DEBUG: Found {owners.count()} owners in database")
            
            for owner in owners:
                # Skip only if explicitly marked as inactive
                is_active = owner.is_active if owner.is_active is not None else True
                status = owner.status if owner.status else 'active'
                
                # Only skip if explicitly inactive
                if is_active is False:
                    continue
                if status == 'inactive':
                    continue
                
                manager_list.append({
                    'id': str(owner.id),
                    'email': owner.email,
                    'mobile': owner.mobile,
                    'name': f"{owner.first_name} {owner.last_name or ''}".strip(),
                    'role': 'owner',
                    'branch_id': None,  # Owners don't have branches
                    'branch_name': 'All Branches'
                })
        else:
            # Get all managers (not owners) - use MongoDB query filtering like staff
            query = Manager.objects(role='manager')
            if branch:
                # Filter by branch ID (more reliable than branch object for MongoEngine ReferenceField)
                query = query.filter(branch=branch.id)
                print(f"DEBUG: Filtering managers by branch: {branch.name} (ID: {branch.id})")
            
            # Get managers with only needed fields
            all_managers = query.only(
                'id', 'email', 'mobile', 'first_name', 'last_name', 'role', 'is_active', 'status', 'branch'
            )
            
            print(f"DEBUG: Query returned {all_managers.count()} managers after filtering")
            
            for manager in all_managers:
                # Skip only if explicitly marked as inactive
                # Handle None/missing values as active (default behavior) - SAME AS STAFF
                is_active = manager.is_active if manager.is_active is not None else True
                status = manager.status if manager.status else 'active'
                
                if is_active is False:
                    print(f"DEBUG: Skipping {manager.first_name} {manager.last_name} - inactive")
                    continue
                if status == 'inactive':
                    print(f"DEBUG: Skipping {manager.first_name} {manager.last_name} - status inactive")
                    continue
                
                # Verify branch match (safety check)
                if branch:
                    if not manager.branch:
                        print(f"DEBUG: Skipping {manager.first_name} {manager.last_name} - no branch assigned")
                        continue
                    manager_branch_id = str(manager.branch.id)
                    selected_branch_id = str(branch.id)
                    if manager_branch_id != selected_branch_id:
                        print(f"DEBUG: ERROR - Manager {manager.first_name} {manager.last_name} branch mismatch!")
                        print(f"  Manager branch: {manager.branch.name} (ID: {manager_branch_id})")
                        print(f"  Selected branch: {branch.name} (ID: {selected_branch_id})")
                        continue
                
                # Get branch name
                branch_name = manager.branch.name if manager.branch else 'No Branch'
                print(f"DEBUG: Adding manager: {manager.first_name} {manager.last_name} ({manager.email}) from {branch_name}")
                
                manager_list.append({
                    'id': str(manager.id),
                    'email': manager.email,
                    'mobile': manager.mobile,
                    'name': f"{manager.first_name} {manager.last_name or ''}".strip(),
                    'role': manager.role or 'manager',
                    'branch_id': str(manager.branch.id) if manager.branch else None,
                    'branch_name': branch_name
                })
        
        # Add same print statement as staff-list for consistency
        print(f"Returning {len(manager_list)} managers for login (branch: {branch.name if branch else 'All'})")

        response = jsonify({
            'managers': manager_list,
            'count': len(manager_list),
            'branch_id': branch_id,
            'branch_name': branch.name if branch else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        
        return response, 200

    except Exception as e:
        print(f"Get manager list error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({
            'error': 'Failed to get manager list',
            'message': str(e),
            'managers': []  # Return empty array on error
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/owner/update-credentials', methods=['PUT', 'OPTIONS'])
@require_auth
def update_owner_credentials(current_user=None):
    """
    Update owner email and password (Owner only)
    
    Request body:
    {
        "email": "owner@example.com" (optional),
        "password": "newpassword" (optional)
    }
    """
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'PUT, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    
    try:
        if not current_user:
            response = jsonify({'error': 'Not authenticated'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 401
        
        # Check if user is Owner
        user_role = current_user.get('role')
        if user_role != 'owner':
            response = jsonify({'error': 'Only Owner can update credentials'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'Request body is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        user_id = current_user.get('user_id')
        owner = Owner.objects(id=user_id).first()
        
        if not owner:
            response = jsonify({'error': 'Owner account not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # Update email if provided
        if 'email' in data and data['email']:
            email = data['email'].strip()
            # Validate email format
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, email):
                response = jsonify({'error': 'Invalid email format'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            
            # Check if email is already taken by another owner
            existing = Owner.objects(email=email).first()
            if existing and str(existing.id) != user_id:
                response = jsonify({'error': 'Email already in use'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            
            owner.email = email
        
        # Update password if provided
        if 'password' in data and data['password']:
            password = data['password'].strip()
            if len(password) < 6:
                response = jsonify({'error': 'Password must be at least 6 characters long'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            
            # Hash and set password
            owner.password_hash = hash_password(password)
        
        owner.updated_at = datetime.utcnow()
        owner.save()
        
        response = jsonify({
            'message': 'Owner credentials updated successfully',
            'user': {
                'id': str(owner.id),
                'email': owner.email,
                'mobile': owner.mobile,
                'first_name': owner.first_name,
                'last_name': owner.last_name,
                'role': 'owner',
                'user_type': 'manager'
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Exception as e:
        print(f"Update owner credentials error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Failed to update credentials', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@auth_bp.route('/switch-branch', methods=['PUT'])
@require_auth
def switch_branch(current_user=None):
    """
    Switch branch for Owner (Owner only)
    
    Request body:
    {
        "branch_id": "branch_id_string"
    }
    """
    try:
        if not current_user:
            response = jsonify({'error': 'Not authenticated'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 401
        
        # Check if user is Owner
        user_role = current_user.get('role')
        if user_role != 'owner':
            response = jsonify({'error': 'Only Owner can switch branches'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'Request body is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch_id = data.get('branch_id')
        if not branch_id:
            response = jsonify({'error': 'branch_id is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        from models import Branch
        from bson import ObjectId
        
        if not ObjectId.is_valid(branch_id):
            response = jsonify({'error': 'Invalid branch ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = Branch.objects(id=branch_id).first()
        if not branch:
            response = jsonify({'error': 'Branch not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        if not branch.is_active:
            response = jsonify({'error': 'Branch is inactive'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Return branch info (actual switching is handled client-side via header)
        response = jsonify({
            'message': 'Branch switched successfully',
            'branch': {
                'id': str(branch.id),
                'name': branch.name,
                'city': branch.city
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Exception as e:
        print(f"Switch branch error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Failed to switch branch', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
