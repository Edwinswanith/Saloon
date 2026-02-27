from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from mongoengine import connect, disconnect
from datetime import datetime, date, time
import os
from urllib.parse import unquote

app = Flask(__name__, static_folder='static', static_url_path='', template_folder='templates')

# Enable response compression (gzip) - reduces transfer sizes by 70-80%
from flask_compress import Compress
Compress(app)
app.config['COMPRESS_MIMETYPES'] = [
    'text/html', 'text/css', 'text/xml', 'text/javascript',
    'application/json', 'application/javascript',
    'application/pdf',  # Add PDF compression for faster downloads
]
app.config['COMPRESS_MIN_SIZE'] = 500

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
# for production
MONGODB_DB = 'Saloon_prod'
# for development
# MONGODB_DB = 'Saloon'

# Connect to MongoDB
try:
    # Build connection URI with database name
    # Remove any existing database name from URI to ensure we use MONGODB_DB
    base_uri = MONGODB_URI
    
    # If URI contains a database path, remove it (we'll add our own)
    if '@' in base_uri:
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            
            # Remove database name from host part if present
            if '/' in host_and_params:
                host = host_and_params.split('/')[0]
                # Keep query parameters if they exist
                if '?' in host_and_params:
                    params = '?' + host_and_params.split('?', 1)[1]
                else:
                    params = ''
                base_uri = f"{credentials}@{host}{params}"
    
    # Add database name to URI if not present
    if f'/{MONGODB_DB}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
        else:
            base_uri = f"{base_uri}/{MONGODB_DB}"
    
    # Add retry and SSL/TLS parameters if not present
    separator = '&' if '?' in base_uri else '?'
    params_to_add = []
    
    if 'retryWrites' not in base_uri:
        params_to_add.append('retryWrites=true')
    if 'w=' not in base_uri:
        params_to_add.append('w=majority')
    if 'tls=' not in base_uri and 'ssl=' not in base_uri:
        params_to_add.append('tls=true')
    
    if params_to_add:
        base_uri = f"{base_uri}{separator}{'&'.join(params_to_add)}"
    
    # Connect with increased timeouts to handle SSL handshake
    # Explicitly specify the database name to avoid defaulting to 'test'
    # Note: SSL/TLS is handled via connection string parameters (tls=true)
    connect(host=base_uri, alias='default', db=MONGODB_DB,
            maxPoolSize=50,  # Increased from 10 to 50 for better concurrency
            minPoolSize=5,   # Increased from 2 to 5 for faster initial connections
            serverSelectionTimeoutMS=30000,  # Increased for SSL handshake
            connectTimeoutMS=30000,  # Increased for SSL handshake
            socketTimeoutMS=30000,  # Increased for SSL handshake
            maxIdleTimeMS=60000,
            waitQueueTimeoutMS=10000)  # Increased wait queue timeout
    print(f"✓ Connected to MongoDB: {MONGODB_DB}")
    print(f"✓ Connection URI: {base_uri.split('@')[0]}@***")
except Exception as e:
    print(f"✗ CRITICAL: MongoDB connection failed: {e}")
    print(f"✗ Database: {MONGODB_DB}")
    print(f"✗ URI: {MONGODB_URI.split('@')[0] if '@' in MONGODB_URI else '***'}@***")
    print("✗ App will continue but ALL database operations will fail!")
    print("✗ Check: 1) MONGODB_URI env var, 2) MongoDB Atlas IP whitelist, 3) Network connectivity")

app.config['JSON_SORT_KEYS'] = False

# Disable strict slashes to avoid 308 redirects that break CORS
app.url_map.strict_slashes = False

# Configure CORS to allow all origins and methods
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Branch-Id", "x-branch-id"]
    }
})

# Initialize Redis cache (if available)
try:
    from utils.redis_cache import init_redis
    init_redis()
except Exception as e:
    print(f"Warning: Redis initialization failed: {e}")
    print("App will continue with in-memory cache fallback.")

# Register Jinja2 template filters for invoice rendering
try:
    from services.invoice_pdf_service import register_template_filters
    register_template_filters(app)
except Exception as e:
    print(f"Warning: Failed to register invoice template filters: {e}")

# Import and register routes (after MongoDB connection)
from routes import register_routes
register_routes(app)

# Register public invoice routes directly on app (without /api prefix)
# These routes are for customer-facing invoice links and should be accessible without /api
from routes.bill_routes import short_invoice_view, short_invoice_pdf, public_invoice_view, public_invoice_pdf
app.add_url_rule('/i/<share_code>', 'short_invoice_view', short_invoice_view, methods=['GET'])
app.add_url_rule('/i/<share_code>/pdf', 'short_invoice_pdf', short_invoice_pdf, methods=['GET'])
app.add_url_rule('/invoice/view/<token>', 'public_invoice_view', public_invoice_view, methods=['GET'])
app.add_url_rule('/invoice/pdf/<token>', 'public_invoice_pdf', public_invoice_pdf, methods=['GET'])

# Register public feedback routes (no /api prefix, no auth required)
from routes.feedback_routes import public_feedback_page, public_feedback_lookup, public_feedback_submit
app.add_url_rule('/feedback', 'public_feedback_page', public_feedback_page, methods=['GET'])
app.add_url_rule('/feedback/lookup', 'public_feedback_lookup', public_feedback_lookup, methods=['POST'])
app.add_url_rule('/feedback/submit', 'public_feedback_submit', public_feedback_submit, methods=['POST'])

# One-time migration: drop old global unique index on customers.mobile
# (replaced with compound index on mobile+branch for multi-branch support)
try:
    from mongoengine.connection import get_db
    db = get_db()
    indexes = db.customers.index_information()
    if 'mobile_1' in indexes:
        db.customers.drop_index('mobile_1')
        print("[MIGRATION] Dropped old global unique index 'mobile_1' on customers collection")
    if 'referral_code_1' in indexes:
        db.customers.drop_index('referral_code_1')
        print("[MIGRATION] Dropped old unique index 'referral_code_1' on customers collection")
    # Drop duplicate appointment index that conflicts with MongoEngine auto-index
    appt_indexes = db.appointments.index_information()
    if 'idx_appointments_staff_date_status_perf' in appt_indexes:
        db.appointments.drop_index('idx_appointments_staff_date_status_perf')
        print("[MIGRATION] Dropped duplicate index 'idx_appointments_staff_date_status_perf' on appointments collection")
except Exception as e:
    pass  # Index may not exist or DB not connected yet

# Serve React static files
# Note: Public invoice routes (/i/<share_code>, /invoice/view/<token>, etc.) are handled separately
# and will match before this catch-all route due to Flask's routing specificity
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Skip public routes - these are handled by dedicated routes
    if path.startswith('i/') or path.startswith('invoice/') or path.startswith('feedback'):
        return jsonify({'error': 'Not found'}), 404
    
    if path != "":
        decoded_path = unquote(path)
        file_path = os.path.join(app.static_folder, decoded_path)
        if os.path.exists(file_path):
            response = send_from_directory(app.static_folder, decoded_path)
            # Cache hashed assets (JS/CSS from Vite) for 1 year
            if any(decoded_path.endswith(ext) for ext in ['.js', '.css']) and '-' in decoded_path:
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            # Cache images/fonts for 30 days
            elif any(decoded_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf']):
                response.headers['Cache-Control'] = 'public, max-age=2592000'
            return response
    response = send_from_directory(app.static_folder, 'index.html')
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.teardown_appcontext
def close_db(error):
    """Close MongoDB connection when app context tears down"""
    pass  # MongoEngine handles connections automatically

if __name__ == '__main__':
    # MongoDB doesn't require create_all() - collections are created on first insert
    # Use PORT environment variable for Cloud Run compatibility
    import os
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    finally:
        disconnect()

