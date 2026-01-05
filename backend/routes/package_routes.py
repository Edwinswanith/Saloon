from flask import Blueprint, request, jsonify
from models import Package, Service
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_auth, require_role
import json

package_bp = Blueprint('package', __name__)

def get_service_details(service_ids):
    """Helper function to get service details from IDs"""
    if not service_ids:
        return []
    
    services = []
    for service_id in service_ids:
        try:
            if ObjectId.is_valid(service_id):
                service = Service.objects.get(id=service_id)
                services.append({
                    'id': str(service.id),
                    'name': service.name,
                    'price': service.price,
                    'duration': service.duration
                })
        except DoesNotExist:
            continue
        except Exception:
            continue
    
    return services

@package_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@package_bp.route('/', methods=['GET'])
def get_packages():
    """Get all packages with optional filters"""
    try:
        status = request.args.get('status')
        search = request.args.get('search')

        query = Package.objects

        # Apply filters
        if status:
            query = query.filter(status=status)
        if search:
            query = query.filter(name__icontains=search)

        # Force evaluation by converting to list
        packages = list(query.order_by('name'))

        response = jsonify([{
            'id': str(p.id),
            'name': p.name,
            'price': p.price,
            'description': p.description,
            'services': json.loads(p.services) if p.services else [],
            'service_details': get_service_details(json.loads(p.services) if p.services else []),
            'status': p.status,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
        } for p in packages])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@package_bp.route('/<id>', methods=['GET'])
def get_package(id):
    """Get a single package by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = Package.objects.get(id=id)
        response = jsonify({
            'id': str(package.id),
            'name': package.name,
            'price': package.price,
            'description': package.description,
            'services': json.loads(package.services) if package.services else [],
            'service_details': get_service_details(json.loads(package.services) if package.services else []),
            'status': package.status,
            'created_at': package.created_at.isoformat() if package.created_at else None,
            'updated_at': package.updated_at.isoformat() if package.updated_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@package_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_package(current_user=None):
    """Create a new package (Manager and Owner only)"""
    try:
        data = request.get_json()

        # Convert services list to JSON string
        services = data.get('services', [])
        services_json = json.dumps(services)

        package = Package(
            name=data['name'],
            price=data['price'],
            description=data.get('description'),
            services=services_json,
            status=data.get('status', 'active')
        )
        package.save()

        response = jsonify({
            'id': str(package.id),
            'message': 'Package created successfully',
            'data': {
                'id': str(package.id),
                'name': package.name,
                'price': package.price
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@package_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_package(id, current_user=None):
    """Update a package (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = Package.objects.get(id=id)
        data = request.get_json()

        package.name = data.get('name', package.name)
        package.price = data.get('price', package.price)
        package.description = data.get('description', package.description)

        # Update services if provided
        if 'services' in data:
            services = data['services']
            package.services = json.dumps(services)

        package.status = data.get('status', package.status)
        package.updated_at = datetime.utcnow()
        package.save()

        response = jsonify({
            'id': str(package.id),
            'message': 'Package updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@package_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_package(id, current_user=None):
    """Soft delete a package (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = Package.objects.get(id=id)
        package.status = 'deleted'
        package.updated_at = datetime.utcnow()
        package.save()

        response = jsonify({'message': 'Package deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@package_bp.route('/active', methods=['GET'])
def get_active_packages():
    """Get all active packages"""
    try:
        packages = Package.objects.filter(status='active').order_by('name')

        response = jsonify([{
            'id': str(p.id),
            'name': p.name,
            'price': p.price,
            'description': p.description,
            'services': json.loads(p.services) if p.services else [],
            'service_details': get_service_details(json.loads(p.services) if p.services else [])
        } for p in packages])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
