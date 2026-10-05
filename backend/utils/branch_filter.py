"""
Branch filtering utilities for multi-branch support
"""
import os

from flask import request
from models import Branch, Staff, Manager, Owner
from bson import ObjectId


def _env_list(name):
    """Return a normalized comma-separated environment variable as a set."""
    return {
        value.strip().lower()
        for value in os.environ.get(name, '').split(',')
        if value.strip()
    }


def get_demo_branch_id():
    """Configured demo branch id, or None when demo isolation is disabled."""
    branch_id = os.environ.get('DEMO_BRANCH_ID', '').strip()
    if branch_id and ObjectId.is_valid(branch_id):
        return branch_id
    return None


def get_demo_branch():
    """Configured demo branch document, or None when unavailable."""
    branch_id = get_demo_branch_id()
    if not branch_id:
        return None
    try:
        return Branch.objects(id=branch_id).first()
    except Exception as e:
        print(f"Warning: Could not load demo branch {branch_id}: {e}")
        return None


def _get_user_id(user):
    if isinstance(user, dict):
        return user.get('user_id') or user.get('id')
    if hasattr(user, 'id'):
        return str(user.id)
    return None


def _load_user_document(user):
    """Load the user document behind a token/dict. Documents are returned as-is."""
    if not user:
        return None

    if not isinstance(user, dict):
        return user

    user_id = _get_user_id(user)
    if not user_id or not ObjectId.is_valid(user_id):
        return None

    try:
        role = user.get('role')
        user_type = user.get('user_type', 'staff')

        if role == 'owner':
            return Owner.objects(id=user_id).first()
        if user_type == 'manager':
            return Manager.objects(id=user_id).first()
        return Staff.objects(id=user_id).first()
    except Exception as e:
        print(f"Warning: Could not load user document for demo check {user_id}: {e}")
        return None


def is_demo_user(user):
    """
    True when the authenticated user should be locked to DEMO_BRANCH_ID.

    A staff/manager assigned to DEMO_BRANCH_ID is automatically treated as demo.
    Owner/demo accounts without a branch can be listed in DEMO_USER_IDS,
    DEMO_USER_EMAILS, or DEMO_USER_MOBILES.
    """
    demo_branch_id = get_demo_branch_id()
    if not demo_branch_id or not user:
        return False

    user_id = _get_user_id(user)
    if user_id and user_id.lower() in _env_list('DEMO_USER_IDS'):
        return True

    doc = _load_user_document(user)
    if not doc:
        return False

    email = getattr(doc, 'email', None)
    mobile = getattr(doc, 'mobile', None)
    if email and email.strip().lower() in _env_list('DEMO_USER_EMAILS'):
        return True
    if mobile and mobile.strip().lower() in _env_list('DEMO_USER_MOBILES'):
        return True

    branch = getattr(doc, 'branch', None)
    try:
        if branch and str(branch.id) == str(demo_branch_id):
            return True
    except Exception:
        pass

    return False


def get_demo_branch_for_user(user):
    """Return the demo branch when this user is demo-locked."""
    if not is_demo_user(user):
        return None
    return get_demo_branch()


def demo_forbidden_response(action='perform this action'):
    return {
        'error': 'Demo account is restricted',
        'message': f'Demo accounts cannot {action}.'
    }


def get_user_branch(user):
    """
    Get branch from user (staff/manager)
    Returns branch if user has assigned branch, None otherwise (Owner)
    
    Args:
        user: Can be either a dict (from JWT token) or a MongoEngine document (Staff/Manager)
    """
    if not user:
        return None
    
    # Handle dict user (from JWT token)
    if isinstance(user, dict):
        try:
            user_id = user.get('user_id')
            user_type = user.get('user_type', 'staff')
            role = user.get('role')
            
            # Owner doesn't have a branch
            if role == 'owner':
                return None
            
            # Load the actual user document from database
            if user_id:
                try:
                    from bson import ObjectId
                    # Validate ObjectId format
                    if not ObjectId.is_valid(user_id):
                        return None
                    
                    if user_type == 'manager':
                        manager = Manager.objects(id=user_id).first()
                        if manager and hasattr(manager, 'branch') and manager.branch:
                            return manager.branch
                    else:
                        staff = Staff.objects(id=user_id).first()
                        if staff and hasattr(staff, 'branch') and staff.branch:
                            return staff.branch
                except Exception as e:
                    # Silently fail - return None
                    print(f"Warning: Could not load user branch for {user_id}: {e}")
                    return None
        except Exception as e:
            # Silently fail - return None
            print(f"Warning: Error in get_user_branch: {e}")
            return None
        
        return None
    
    # Handle MongoEngine document
    try:
        if hasattr(user, 'branch') and user.branch:
            return user.branch
    except Exception:
        pass
    
    # Owner or user without branch assignment
    return None


def get_selected_branch(request_obj, user):
    """
    Get selected branch from request header or user's assigned branch
    Priority:
    1. X-Branch-Id header (for Owner switching branches)
    2. User's assigned branch (for Staff/Manager)
    3. None (should not happen for authenticated users)
    
    Args:
        request_obj: Flask request object
        user: Can be either a dict (from JWT token) or a MongoEngine document (Staff/Manager)
    """
    if not user:
        print("[BRANCH_FILTER] No user provided, returning None")
        return None
    
    # Get user role (handle both dict and document)
    user_role = None
    if isinstance(user, dict):
        user_role = user.get('role')
        user_id = user.get('user_id', 'unknown')
    elif hasattr(user, 'role'):
        user_role = user.role
        user_id = str(user.id) if hasattr(user, 'id') else 'unknown'
    else:
        user_id = 'unknown'
    
    print(f"[BRANCH_FILTER] User: {user_id}, Role: {user_role}")

    demo_branch = get_demo_branch_for_user(user)
    if demo_branch:
        print(
            f"[BRANCH_FILTER] Demo user locked to branch: "
            f"{demo_branch.name} (ID: {demo_branch.id})"
        )
        return demo_branch
    
    # Check for branch_id in header (Owner can switch branches)
    branch_id_header = request_obj.headers.get('X-Branch-Id') or request_obj.headers.get('x-branch-id')
    print(f"[BRANCH_FILTER] X-Branch-Id header: {branch_id_header}")
    
    if branch_id_header:
        try:
            # Validate ObjectId format
            if ObjectId.is_valid(branch_id_header):
                branch = Branch.objects(id=branch_id_header).first()
                if branch:
                    # Any authenticated user (staff/manager/owner) can pick any active branch.
                    # The original assigned branch is no longer enforced — every staff member
                    # is allowed to log in and work at any branch.
                    print(f"[BRANCH_FILTER] {user_role or 'user'} accessing branch from header: {branch.name}")
                    return branch
                else:
                    print(f"[BRANCH_FILTER] Branch not found for ID: {branch_id_header}")
            else:
                print(f"[BRANCH_FILTER] Invalid ObjectId format in header: {branch_id_header}")
        except Exception as e:
            print(f"[BRANCH_FILTER] Error processing header branch: {e}")
    
    # Fall back to user's assigned branch
    user_branch = get_user_branch(user)
    if user_branch:
        print(f"[BRANCH_FILTER] Using user's assigned branch: {user_branch.name} (ID: {user_branch.id})")
    else:
        print(f"[BRANCH_FILTER] No branch found for user. Role: {user_role}")
    return user_branch


def filter_by_branch(query, branch):
    """
    Add branch filter to query - STRICTLY excludes null branch customers
    Always excludes customers with null branch_id to prevent mixed data
    """
    if branch:
        # Filter by branch AND explicitly exclude customers with null branch_id
        return query.filter(branch=branch).filter(branch__ne=None)
    # If no branch specified, still exclude null branch customers for safety
    return query.filter(branch__ne=None)


def require_branch_access(branch_id, user):
    """
    Check if user can access the specified branch.

    All authenticated users (staff/manager/owner) can access any active branch.
    Staff are pooled across the business and may sign in to and work at any branch.
    Returns (allowed: bool, branch: Branch or None).
    """
    if not user or not branch_id:
        return False, None

    try:
        demo_branch = get_demo_branch_for_user(user)
        if demo_branch:
            if str(demo_branch.id) == str(branch_id):
                return True, demo_branch
            return False, None

        if not ObjectId.is_valid(branch_id):
            return False, None

        branch = Branch.objects(id=branch_id).first()
        if not branch:
            return False, None

        return True, branch
    except Exception:
        return False, None


def get_branch_id_from_request(request_obj, user):
    """
    Get branch_id string from request or user
    Returns branch_id as string or None
    """
    branch = get_selected_branch(request_obj, user)
    if branch:
        return str(branch.id)
    return None

