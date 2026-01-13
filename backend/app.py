from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from mongoengine import connect, disconnect
from datetime import datetime, date, time
import os
from urllib.parse import unquote

app = Flask(__name__, static_folder='static', static_url_path='')

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
    
    # Add retry parameters if not present
    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
    
    # Connect with increased timeouts to handle SSL handshake
    # Explicitly specify the database name to avoid defaulting to 'test'
    connect(host=base_uri, alias='default', db=MONGODB_DB,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000)
    print(f"Connected to MongoDB: {MONGODB_DB}")
except Exception as e:
    print(f"Warning: MongoDB connection failed: {e}")
    print("App will continue but database operations may fail.")

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

# Import and register routes (after MongoDB connection)
from routes import register_routes
register_routes(app)

# Serve React static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "":
        # Decode URL-encoded path (e.g., %20 -> space)
        decoded_path = unquote(path)
        file_path = os.path.join(app.static_folder, decoded_path)
        if os.path.exists(file_path):
            return send_from_directory(app.static_folder, decoded_path)
    return send_from_directory(app.static_folder, 'index.html')

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

