"""
Sorting utilities for Flask routes
"""
from flask import request


def apply_sorting(query, default_sort='-created_at'):
    """
    Apply sorting to a MongoEngine query based on request parameters
    
    Args:
        query: MongoEngine query object
        default_sort: Default sort field (with '-' prefix for descending)
    
    Returns:
        Query with sorting applied
    
    Usage:
        query = Customer.objects
        query = apply_sorting(query, default_sort='-created_at')
    """
    sort_by = request.args.get('sort_by', default_sort.lstrip('-'))
    sort_order = request.args.get('sort_order', 'desc' if default_sort.startswith('-') else 'asc')
    
    # Validate sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc' if default_sort.startswith('-') else 'asc'
    
    # Apply sort
    order_field = f"-{sort_by}" if sort_order == 'desc' else sort_by
    return query.order_by(order_field)


def get_pagination_params(default_per_page=20, max_per_page=100):
    """
    Get pagination parameters from request
    
    Args:
        default_per_page: Default items per page
        max_per_page: Maximum items per page
    
    Returns:
        tuple: (page, per_page)
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', default_per_page, type=int), max_per_page)
    
    # Ensure page is at least 1
    page = max(1, page)
    
    return page, per_page

