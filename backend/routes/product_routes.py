from flask import Blueprint, request, jsonify
from models import Product, ProductCategory
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

product_bp = Blueprint('product', __name__)

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

@product_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Product Category Routes

@product_bp.route('/categories', methods=['GET'])
def get_product_categories():
    """Get all product categories"""
    try:
        # Force evaluation by converting to list
        categories = list(ProductCategory.objects.order_by('display_order'))
        response = jsonify([{
            'id': str(cat.id),
            'name': cat.name,
            'display_order': cat.display_order,
            'created_at': cat.created_at.isoformat() if cat.created_at else None
        } for cat in categories])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@product_bp.route('/categories', methods=['POST'])
@require_role('manager', 'owner')
def create_product_category(current_user=None):
    """Create a new product category (Manager and Owner only)"""
    try:
        data = request.get_json()

        category = ProductCategory(
            name=data['name'],
            display_order=data.get('display_order', 0)
        )
        category.save()

        response = jsonify({
            'id': str(category.id),
            'message': 'Product category created successfully',
            'data': {
                'id': str(category.id),
                'name': category.name,
                'display_order': category.display_order
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@product_bp.route('/categories/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_product_category(id, current_user=None):
    """Update a product category (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid category ID format'}), 400
        
        category = ProductCategory.objects.get(id=id)
        data = request.get_json()

        category.name = data.get('name', category.name)
        category.display_order = data.get('display_order', category.display_order)
        category.save()

        response = jsonify({
            'id': str(category.id),
            'message': 'Product category updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Category not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@product_bp.route('/categories/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_product_category(id, current_user=None):
    """Delete a product category (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid category ID format'}), 400
        
        category = ProductCategory.objects.get(id=id)

        # Check if category has products
        product_count = Product.objects(category=category).count()
        if product_count > 0:
            response = jsonify({'error': 'Cannot delete category with associated products'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        category.delete()

        response = jsonify({'message': 'Product category deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Category not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Product Routes

@product_bp.route('/', methods=['GET'])
@require_auth
def get_products(current_user=None):
    """Get all products with optional filters, filtered by branch"""
    try:
        # Query parameters
        category_id = request.args.get('category_id', type=str)
        status = request.args.get('status')
        search = request.args.get('search')
        low_stock = request.args.get('low_stock', type=bool)

        # Filter by status='active' by default - only show active products
        query = Product.objects(status='active')

        # Filter by branch - strict filtering, only show products belonging to selected branch
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if category_id and ObjectId.is_valid(category_id):
            try:
                category = ProductCategory.objects.get(id=category_id)
                query = query.filter(category=category)
            except DoesNotExist:
                pass
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
        
        # Get total count before pagination (for low_stock, we'll filter after)
        total = query.count()
        
        # Apply pagination
        products = list(query.skip((page - 1) * per_page).limit(per_page))
        
        # Apply low_stock filter in Python (complex logic requires checking each product)
        if low_stock:
            products = [p for p in products if p.stock_quantity and p.min_stock_level and p.stock_quantity <= p.min_stock_level]
            # Update total for low_stock filter
            total = len(products)

        return jsonify({
            'data': [{
                'id': str(p.id),
                'name': p.name,
                'category_id': str(p.category.id) if p.category else None,
                'category_name': p.category.name if p.category else None,
                'price': p.price,
                'cost': p.cost,
                'stock_quantity': p.stock_quantity,
                'min_stock_level': p.min_stock_level,
                'sku': p.sku,
                'description': p.description,
                'status': p.status,
                'low_stock': (p.stock_quantity or 0) <= (p.min_stock_level or 0) if p.min_stock_level else False,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'branch_id': str(p.branch.id) if p.branch else None
            } for p in products],
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<id>', methods=['GET'])
def get_product(id):
    """Get a single product by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid product ID format'}), 400
        
        product = Product.objects.get(id=id)
        return jsonify({
            'id': str(product.id),
            'name': product.name,
            'category_id': str(product.category.id) if product.category else None,
            'category_name': product.category.name if product.category else None,
            'price': product.price,
            'cost': product.cost,
            'stock_quantity': product.stock_quantity,
            'min_stock_level': product.min_stock_level,
            'sku': product.sku,
            'description': product.description,
            'status': product.status,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/', methods=['POST'])
@require_role('staff', 'manager', 'owner')
def create_product(current_user=None):
    """Create a new product (Staff, Manager and Owner)"""
    try:
        data = request.get_json()

        # Get branch for the product
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required to create a product'}), 400

        # Get category reference
        category = None
        if data.get('category_id'):
            if not ObjectId.is_valid(data['category_id']):
                return jsonify({'error': 'Invalid category ID format'}), 400
            try:
                category = ProductCategory.objects.get(id=data['category_id'])
            except DoesNotExist:
                return jsonify({'error': 'Category not found'}), 400

        product = Product(
            name=data['name'],
            category=category,
            price=data['price'],
            cost=data.get('cost', 0),
            stock_quantity=data.get('stock_quantity', 0),
            min_stock_level=data.get('min_stock_level', 0),
            sku=data.get('sku'),
            description=data.get('description'),
            branch=branch,
            status=data.get('status', 'active')
        )
        product.save()

        return jsonify({
            'id': str(product.id),
            'message': 'Product created successfully',
            'data': {
                'id': str(product.id),
                'name': product.name,
                'price': product.price
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<id>', methods=['PUT'])
@require_role('staff', 'manager', 'owner')
def update_product(id, current_user=None):
    """Update a product (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid product ID format'}), 400
        
        product = Product.objects.get(id=id)
        
        # Verify branch access
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400
        
        is_valid, error_msg = verify_branch_access(product, branch, 'Product')
        if not is_valid:
            return jsonify({'error': error_msg}), 403
        
        data = request.get_json()

        product.name = data.get('name', product.name)
        
        # Update category if provided
        if 'category_id' in data:
            if data['category_id']:
                if not ObjectId.is_valid(data['category_id']):
                    return jsonify({'error': 'Invalid category ID format'}), 400
                try:
                    product.category = ProductCategory.objects.get(id=data['category_id'])
                except DoesNotExist:
                    return jsonify({'error': 'Category not found'}), 400
            else:
                product.category = None
        
        product.price = data.get('price', product.price)
        product.cost = data.get('cost', product.cost)
        product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
        product.min_stock_level = data.get('min_stock_level', product.min_stock_level)
        product.sku = data.get('sku', product.sku)
        product.description = data.get('description', product.description)
        product.status = data.get('status', product.status)
        product.updated_at = datetime.utcnow()
        product.save()

        return jsonify({
            'id': str(product.id),
            'message': 'Product updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_product(id, current_user=None):
    """Soft delete a product (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid product ID format'}), 400
        
        product = Product.objects.get(id=id)
        
        # Verify branch access
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400
        
        is_valid, error_msg = verify_branch_access(product, branch, 'Product')
        if not is_valid:
            return jsonify({'error': error_msg}), 403
        
        product.status = 'deleted'
        product.updated_at = datetime.utcnow()
        product.save()

        return jsonify({'message': 'Product deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/low-stock', methods=['GET'])
@require_auth
def get_low_stock_products(current_user=None):
    """Get products with stock below minimum level, filtered by branch"""
    try:
        query = Product.objects(status='active')

        # Filter by branch - strict filtering, only show products belonging to selected branch
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        # Force evaluation by converting to list
        products = list(query.order_by('stock_quantity'))

        # Filter for low stock in Python (MongoEngine doesn't support field comparison)
        low_stock_products = [
            p for p in products
            if p.stock_quantity is not None and p.min_stock_level is not None
            and p.stock_quantity <= p.min_stock_level
        ]

        return jsonify([{
            'id': str(p.id),
            'name': p.name,
            'category_name': p.category.name if p.category else None,
            'stock_quantity': p.stock_quantity,
            'min_stock_level': p.min_stock_level,
            'deficit': p.min_stock_level - p.stock_quantity
        } for p in low_stock_products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
