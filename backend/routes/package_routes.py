from flask import Blueprint, request, jsonify
from models import Package, Service
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch
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

def verify_branch_access(item, branch, item_type='item'):
    """Verify that an item belongs to the specified branch"""
    if not branch:
        return False, 'Branch is required'
    if not item:
        return False, f'{item_type} not found'
    if not item.branch:
        return False, f'{item_type} has no branch assigned (legacy data)'
    if str(item.branch.id) != str(branch.id):
        return False, f'{item_type} belongs to a different branch'
    return True, None

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
@require_auth
def get_packages(current_user=None):
    """Get all packages with optional filters, filtered by branch"""
    try:
        status = request.args.get('status')
        search = request.args.get('search')

        # Filter by status='active' by default - only show active packages
        query = Package.objects(status='active')
        
        print(f"[PACKAGE GET] Initial query count (active only): {query.count()}")

        # Filter by branch - strict filtering, only show packages belonging to selected branch
        branch = get_selected_branch(request, current_user)
        if branch:
            print(f"[PACKAGE GET] Filtering by branch: {branch.name} (ID: {branch.id})")
            query = query.filter(branch=branch)
            print(f"[PACKAGE GET] After branch filter count: {query.count()}")
        else:
            print(f"[PACKAGE GET] WARNING: No branch found for user. Packages may be empty.")

        # Apply filters
        # Allow status override if explicitly requested (e.g., for admin views)
        if status:
            query = query.filter(status=status)
        if search:
            query = query.filter(name__icontains=search)

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Apply sorting
        order_field = f"-{sort_by}" if sort_order == 'desc' else sort_by
        query = query.order_by(order_field)
        
        # Get total count before pagination
        total = query.count()
        print(f"[PACKAGE GET] Total packages found: {total}")
        
        # Apply pagination
        packages = list(query.skip((page - 1) * per_page).limit(per_page))
        print(f"[PACKAGE GET] Returning {len(packages)} packages (page {page}, per_page {per_page})")

        response = jsonify({
            'data': [{
                'id': str(p.id),
                'name': p.name,
                'price': p.price,
                'description': p.description,
                'services': json.loads(p.services) if p.services else [],
                'service_details': get_service_details(json.loads(p.services) if p.services else []),
                'status': p.status,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                'branch_id': str(p.branch.id) if p.branch else None
            } for p in packages],
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
            }
        })
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
@require_role('staff', 'manager', 'owner')
def create_package(current_user=None):
    """Create a new package (Staff, Manager and Owner)"""
    try:
        data = request.get_json()

        # Get branch for the package
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required to create a package'}), 400

        # Convert services list to JSON string
        services = data.get('services', [])
        services_json = json.dumps(services)

        package = Package(
            name=data['name'],
            price=data['price'],
            description=data.get('description'),
            services=services_json,
            branch=branch,
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
@require_role('staff', 'manager', 'owner')
def update_package(id, current_user=None):
    """Update a package (Staff, Manager and Owner)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = Package.objects.get(id=id)
        
        # Verify branch access
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        is_valid, error_msg = verify_branch_access(package, branch, 'Package')
        if not is_valid:
            response = jsonify({'error': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
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
        
        # Verify branch access
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        is_valid, error_msg = verify_branch_access(package, branch, 'Package')
        if not is_valid:
            response = jsonify({'error': error_msg})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403
        
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
@require_auth
def get_active_packages(current_user=None):
    """Get all active packages, filtered by branch"""
    try:
        query = Package.objects.filter(status='active')

        # Filter by branch - strict filtering, only show packages belonging to selected branch
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        packages = list(query.order_by('name'))

        response = jsonify([{
            'id': str(p.id),
            'name': p.name,
            'price': p.price,
            'description': p.description,
            'services': json.loads(p.services) if p.services else [],
            'service_details': get_service_details(json.loads(p.services) if p.services else []),
            'branch_id': str(p.branch.id) if p.branch else None
        } for p in packages])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
