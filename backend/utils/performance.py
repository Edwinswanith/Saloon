"""
Performance logging utility for Flask endpoints
"""
import time
from functools import wraps


def log_performance(f):
    """
    Decorator to log endpoint execution time
    
    Usage:
        @log_performance
        @app.route('/api/data')
        def get_data():
            return jsonify({'data': 'value'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start
        
        # Log performance (can be upgraded to use proper logging framework)
        print(f"[PERF] {f.__name__}: {duration:.3f}s")
        
        # Optionally add header with timing info
        if hasattr(result, 'headers'):
            result.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return result
    return decorated_function

