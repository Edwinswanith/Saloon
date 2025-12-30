"""
Utility functions for generating and managing discount approval codes
Phase 5: Discount Control & Approval Workflow
"""
import secrets
import hashlib
from datetime import datetime, timedelta

def generate_approval_code(length=8):
    """
    Generate a random approval code
    
    Args:
        length: Length of the code (default: 8)
    
    Returns:
        str: Random alphanumeric code
    """
    # Generate a secure random code
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Excludes confusing characters
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    return code

def hash_approval_code(code):
    """
    Hash an approval code using SHA-256
    
    Args:
        code: Plain text approval code
    
    Returns:
        str: Hashed code (hex digest)
    """
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

def verify_approval_code(code, code_hash):
    """
    Verify an approval code against its hash
    
    Args:
        code: Plain text approval code to verify
        code_hash: Stored hash to compare against
    
    Returns:
        bool: True if code matches hash, False otherwise
    """
    computed_hash = hash_approval_code(code)
    return computed_hash == code_hash

def is_code_expired(expires_at):
    """
    Check if an approval code has expired
    
    Args:
        expires_at: DateTime when code expires (None if no expiration)
    
    Returns:
        bool: True if expired, False otherwise
    """
    if expires_at is None:
        return False
    return datetime.utcnow() > expires_at

def can_use_code(usage_count, max_uses):
    """
    Check if code can still be used based on usage limits
    
    Args:
        usage_count: Current usage count
        max_uses: Maximum allowed uses (None if unlimited)
    
    Returns:
        bool: True if code can be used, False otherwise
    """
    if max_uses is None:
        return True
    return usage_count < max_uses

