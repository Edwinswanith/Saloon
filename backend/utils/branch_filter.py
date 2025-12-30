"""
Branch filtering utilities for multi-branch support
"""
from flask import request
from models import Branch, Staff, Manager
from bson import ObjectId


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
        return None
    
    # Get user role (handle both dict and document)
    user_role = None
    if isinstance(user, dict):
        user_role = user.get('role')
    elif hasattr(user, 'role'):
        user_role = user.role
    
    # Check for branch_id in header (Owner can switch branches)
    branch_id_header = request_obj.headers.get('X-Branch-Id')
    if branch_id_header:
        try:
            # Validate ObjectId format
            if ObjectId.is_valid(branch_id_header):
                branch = Branch.objects(id=branch_id_header).first()
                if branch:
                    # Check if user is Owner (can access any branch)
                    if user_role == 'owner':
                        return branch
                    # Check if user's branch matches
                    user_branch = get_user_branch(user)
                    if user_branch and str(user_branch.id) == branch_id_header:
                        return branch
        except Exception:
            pass
    
    # Fall back to user's assigned branch
    return get_user_branch(user)


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
    Check if user can access the specified branch
    Returns (allowed: bool, branch: Branch or None)
    
    Args:
        branch_id: Branch ID as string
        user: Can be either a dict (from JWT token) or a MongoEngine document (Staff/Manager)
    """
    if not user or not branch_id:
        return False, None
    
    try:
        if not ObjectId.is_valid(branch_id):
            return False, None
        
        branch = Branch.objects(id=branch_id).first()
        if not branch:
            return False, None
        
        # Get user role (handle both dict and document)
        user_role = None
        if isinstance(user, dict):
            user_role = user.get('role')
        elif hasattr(user, 'role'):
            user_role = user.role
        
        # Owner can access any branch
        if user_role == 'owner':
            return True, branch
        
        # Staff/Manager can only access their assigned branch
        user_branch = get_user_branch(user)
        if user_branch and str(user_branch.id) == branch_id:
            return True, branch
        
        return False, None
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

