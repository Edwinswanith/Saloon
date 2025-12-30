"""
Authentication utilities for JWT token handling and password hashing
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import os

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def hash_password(password):
    """
    Hash a password using bcrypt

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password
    """
    if not password:
        return None

    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, password_hash):
    """
    Verify a password against its hash

    Args:
        password (str): Plain text password
        password_hash (str): Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def generate_jwt_token(user_id, role, user_type='staff', name=''):
    """
    Generate a JWT token for a user

    Args:
        user_id (str): User's MongoDB ObjectId as string
        role (str): User role (staff, manager, owner)
        user_type (str): Type of user (staff or manager)
        name (str): User's full name

    Returns:
        str: JWT token
    """
    payload = {
        'user_id': str(user_id),
        'role': role,
        'user_type': user_type,
        'name': name,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token):
    """
    Verify and decode a JWT token

    Args:
        token (str): JWT token

    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """
    Get the current authenticated user from request context

    Returns:
        dict: User info from JWT token or None
    """
    # Try to get token from Authorization header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None

    # Expected format: "Bearer <token>"
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]
    return verify_jwt_token(token)


def require_auth(f):
    """
    Decorator to require authentication for a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if not user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401

        # Add user to kwargs for route handler
        kwargs['current_user'] = user
        return f(*args, **kwargs)

    return decorated_function


def require_role(*allowed_roles):
    """
    Decorator to require specific role(s) for a route

    Args:
        *allowed_roles: Variable number of allowed roles (e.g., 'manager', 'owner')

    Usage:
        @require_role('manager', 'owner')
        def protected_route():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401

            user_role = user.get('role')

            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'This action requires {" or ".join(allowed_roles)} role',
                    'your_role': user_role
                }), 403

            # Add user to kwargs for route handler
            kwargs['current_user'] = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def optional_auth(f):
    """
    Decorator for routes where authentication is optional
    Adds current_user to kwargs if authenticated, None otherwise
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        kwargs['current_user'] = user
        return f(*args, **kwargs)

    return decorated_function
