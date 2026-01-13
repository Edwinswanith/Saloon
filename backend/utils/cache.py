"""
Response caching utility for Flask endpoints

Simple in-memory cache implementation. Can be upgraded to Redis later for distributed systems.
"""
from functools import wraps
from flask import request, jsonify
import hashlib
import time

# Simple in-memory cache store
cache_store = {}
CACHE_TTL = 300  # Default: 5 minutes


def cache_response(ttl=CACHE_TTL):
    """
    Decorator to cache Flask endpoint responses
    
    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
    
    Usage:
        @cache_response(ttl=300)
        @app.route('/api/data')
        def get_data():
            return jsonify({'data': 'value'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from endpoint path + query params
            cache_key = f"{request.path}:{request.query_string.decode()}"
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Check cache
            if cache_key_hash in cache_store:
                cached_data, timestamp = cache_store[cache_key_hash]
                if (time.time() - timestamp) < ttl:
                    # Return cached response
                    return jsonify(cached_data)
                else:
                    # Cache expired, remove it
                    del cache_store[cache_key_hash]
            
            # Execute function
            try:
                result = f(*args, **kwargs)
                
                # Don't cache error responses (status codes >= 400)
                if isinstance(result, tuple) and len(result) == 2:
                    response_obj, status_code = result
                    if status_code >= 400:
                        return result
                    # Cache successful responses only
                    if hasattr(response_obj, 'get_json'):
                        try:
                            cache_store[cache_key_hash] = (response_obj.get_json(), time.time())
                        except Exception:
                            # If JSON parsing fails, don't cache
                            pass
                    return result
                
                # Cache result if it's a JSON response (success case)
                if hasattr(result, 'get_json'):
                    try:
                        cache_store[cache_key_hash] = (result.get_json(), time.time())
                    except Exception:
                        # If JSON parsing fails, don't cache
                        pass
                
                return result
            except Exception as e:
                # Don't cache errors, just re-raise
                raise
        return decorated_function
    return decorator


def clear_cache(pattern=None):
    """
    Clear cache entries
    
    Args:
        pattern: Optional pattern to match cache keys (not implemented in simple version)
                 If None, clears all cache
    """
    if pattern is None:
        cache_store.clear()
    else:
        # In simple version, clear all if pattern provided
        # In Redis version, would use pattern matching
        cache_store.clear()


def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        dict with cache statistics
    """
    return {
        'size': len(cache_store),
        'entries': list(cache_store.keys())[:10]  # First 10 keys as sample
    }

