"""
Redis-based response caching utility for Flask endpoints
Falls back to in-memory cache if Redis is not available

Usage:
    from utils.redis_cache import cache_response, init_redis
    
    # Initialize Redis (call once at app startup)
    init_redis()
    
    # Use decorator
    @cache_response(ttl=300)
    @app.route('/api/data')
    def get_data():
        return jsonify({'data': 'value'})
"""

from functools import wraps
from flask import request, jsonify
import hashlib
import time
import json
import os

# Try to import redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Fallback in-memory cache store
fallback_cache_store = {}
CACHE_TTL = 300  # Default: 5 minutes

# Redis client (initialized by init_redis)
redis_client = None


def init_redis():
    """
    Initialize Redis connection
    Call this once at app startup (e.g., in app.py)
    """
    global redis_client
    
    if not REDIS_AVAILABLE:
        print("[CACHE] Redis not available (package not installed), using in-memory cache")
        return False
    
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        print("[CACHE] REDIS_URL not set, using in-memory cache")
        return False
    
    try:
        redis_client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # Test connection
        redis_client.ping()
        print(f"[CACHE] Redis connected successfully: {redis_url}")
        return True
    except Exception as e:
        print(f"[CACHE] Redis connection failed: {e}, using in-memory cache")
        redis_client = None
        return False


def cache_response(ttl=CACHE_TTL):
    """
    Decorator to cache Flask endpoint responses
    
    Uses Redis if available, otherwise falls back to in-memory cache.
    
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
            # Create cache key from endpoint path + query params (excluding cache-busting _t param)
            # Also include branch header for branch-specific caching
            query_params = {k: v for k, v in request.args.items() if k != '_t'}
            sorted_params = sorted(query_params.items())
            branch_id = request.headers.get('x-branch-id', '')
            cache_key = f"{request.path}:{sorted_params}:{branch_id}"
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try Redis first
            if redis_client:
                try:
                    cached_data = redis_client.get(f"cache:{cache_key_hash}")
                    if cached_data:
                        return jsonify(json.loads(cached_data))
                except Exception as e:
                    # Redis error, fall back to in-memory
                    print(f"[CACHE] Redis error: {e}, falling back to in-memory")
            
            # Fallback to in-memory cache
            if cache_key_hash in fallback_cache_store:
                cached_data, timestamp = fallback_cache_store[cache_key_hash]
                if (time.time() - timestamp) < ttl:
                    return jsonify(cached_data)
                else:
                    # Cache expired, remove it
                    del fallback_cache_store[cache_key_hash]
            
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
                            data = response_obj.get_json()
                            # Store in Redis
                            if redis_client:
                                try:
                                    redis_client.setex(
                                        f"cache:{cache_key_hash}",
                                        ttl,
                                        json.dumps(data)
                                    )
                                except Exception:
                                    pass  # Redis error, continue with in-memory
                            
                            # Store in fallback cache
                            fallback_cache_store[cache_key_hash] = (data, time.time())
                        except Exception:
                            # If JSON parsing fails, don't cache
                            pass
                    return result
                
                # Cache result if it's a JSON response (success case)
                if hasattr(result, 'get_json'):
                    try:
                        data = result.get_json()
                        # Store in Redis
                        if redis_client:
                            try:
                                redis_client.setex(
                                    f"cache:{cache_key_hash}",
                                    ttl,
                                    json.dumps(data)
                                )
                            except Exception:
                                pass  # Redis error, continue with in-memory
                        
                        # Store in fallback cache
                        fallback_cache_store[cache_key_hash] = (data, time.time())
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
        pattern: Optional pattern to match cache keys
                 If None, clears all cache
    """
    if redis_client:
        try:
            if pattern:
                keys = redis_client.keys(f"cache:*{pattern}*")
                if keys:
                    redis_client.delete(*keys)
            else:
                # Clear all cache keys
                keys = redis_client.keys("cache:*")
                if keys:
                    redis_client.delete(*keys)
        except Exception as e:
            print(f"[CACHE] Error clearing Redis cache: {e}")
    
    # Clear fallback cache
    if pattern:
        # Simple pattern matching for in-memory cache
        keys_to_delete = [k for k in fallback_cache_store.keys() if pattern in str(k)]
        for k in keys_to_delete:
            del fallback_cache_store[k]
    else:
        fallback_cache_store.clear()


def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        dict with cache statistics
    """
    stats = {
        'type': 'redis' if redis_client else 'in-memory',
        'size': 0,
        'entries': []
    }
    
    if redis_client:
        try:
            keys = redis_client.keys("cache:*")
            stats['size'] = len(keys)
            stats['entries'] = [k for k in keys[:10]]  # First 10 keys as sample
        except Exception:
            pass
    else:
        stats['size'] = len(fallback_cache_store)
        stats['entries'] = list(fallback_cache_store.keys())[:10]
    
    return stats

