from flask import Blueprint, request, jsonify
from models import Asset
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

asset_bp = Blueprint('asset', __name__)

@asset_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@asset_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_assets(current_user=None):
    """Get all assets with optional filters (Manager and Owner only)"""
    try:
        # Query parameters
        category = request.args.get('category')
        status = request.args.get('status')
        location = request.args.get('location')
        search = request.args.get('search')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Asset.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if category:
            query = query.filter(category=category)
        if status:
            query = query.filter(status=status)
        if location:
            query = query.filter(location=location)
        if search:
            query = query.filter(name__icontains=search)

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Apply sorting
        order_field = f"-{sort_by}" if sort_order == 'desc' else sort_by
        query = query.order_by(order_field)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        assets = list(query.skip((page - 1) * per_page).limit(per_page))

        response = jsonify({
            'data': [{
            'id': str(a.id),
            'name': a.name,
            'category': a.category,
            'purchase_date': a.purchase_date.isoformat() if a.purchase_date else None,
            'purchase_price': a.purchase_price,
            'current_value': a.current_value,
            'depreciation_rate': a.depreciation_rate,
            'status': a.status,
            'location': a.location,
            'description': a.description,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in assets],
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

@asset_bp.route('/<id>', methods=['GET'])
@require_role('manager', 'owner')
def get_asset(id, current_user=None):
    """Get a single asset by ID (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid asset ID format'}), 400
        
        asset = Asset.objects.get(id=id)
        response = jsonify({
            'id': str(asset.id),
            'name': asset.name,
            'category': asset.category,
            'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
            'purchase_price': asset.purchase_price,
            'current_value': asset.current_value,
            'depreciation_rate': asset.depreciation_rate,
            'status': asset.status,
            'location': asset.location,
            'description': asset.description,
            'created_at': asset.created_at.isoformat() if asset.created_at else None,
            'updated_at': asset.updated_at.isoformat() if asset.updated_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@asset_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_asset(current_user=None):
    """Create a new asset (Manager and Owner only)"""
    try:
        data = request.get_json()

        # Parse purchase date if provided
        purchase_date = None
        if 'purchase_date' in data and data['purchase_date']:
            purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()

        asset = Asset(
            name=data['name'],
            category=data.get('category'),
            purchase_date=purchase_date,
            purchase_price=data.get('purchase_price'),
            current_value=data.get('current_value'),
            depreciation_rate=data.get('depreciation_rate'),
            status=data.get('status', 'active'),
            location=data.get('location'),
            description=data.get('description')
        )
        asset.save()

        response = jsonify({
            'id': str(asset.id),
            'message': 'Asset created successfully',
            'data': {
                'id': str(asset.id),
                'name': asset.name
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@asset_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_asset(id, current_user=None):
    """Update an asset (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid asset ID format'}), 400
        
        asset = Asset.objects.get(id=id)
        data = request.get_json()

        asset.name = data.get('name', asset.name)
        asset.category = data.get('category', asset.category)

        # Update purchase date if provided
        if 'purchase_date' in data:
            if data['purchase_date']:
                asset.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
            else:
                asset.purchase_date = None

        asset.purchase_price = data.get('purchase_price', asset.purchase_price)
        asset.current_value = data.get('current_value', asset.current_value)
        asset.depreciation_rate = data.get('depreciation_rate', asset.depreciation_rate)
        asset.status = data.get('status', asset.status)
        asset.location = data.get('location', asset.location)
        asset.description = data.get('description', asset.description)
        asset.updated_at = datetime.utcnow()
        asset.save()

        response = jsonify({
            'id': str(asset.id),
            'message': 'Asset updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@asset_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_asset(id, current_user=None):
    """Delete an asset (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid asset ID format'}), 400
        
        asset = Asset.objects.get(id=id)
        asset.delete()

        response = jsonify({'message': 'Asset deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@asset_bp.route('/summary', methods=['GET'])
def get_assets_summary():
    """Get summary of assets by category and status"""
    try:
        assets = list(Asset.objects)

        # Group by category
        categories = {}
        total_purchase_value = 0
        total_current_value = 0

        for asset in assets:
            category = asset.category or 'Uncategorized'
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'total_purchase_price': 0,
                    'total_current_value': 0
                }

            categories[category]['count'] += 1

            if asset.purchase_price:
                categories[category]['total_purchase_price'] += asset.purchase_price
                total_purchase_value += asset.purchase_price

            if asset.current_value:
                categories[category]['total_current_value'] += asset.current_value
                total_current_value += asset.current_value

        # Count by status
        status_counts = {}
        for asset in assets:
            status = asset.status or 'unknown'
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        return jsonify({
            'total_assets': len(assets),
            'total_purchase_value': total_purchase_value,
            'total_current_value': total_current_value,
            'by_category': categories,
            'by_status': status_counts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@asset_bp.route('/categories', methods=['GET'])
def get_asset_categories():
    """Get list of unique asset categories"""
    try:
        assets = Asset.objects.filter(category__ne=None)
        categories = list(set([a.category for a in assets if a.category]))

        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
