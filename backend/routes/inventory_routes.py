from flask import Blueprint, request, jsonify
from models import Supplier, Order, OrderItemEmbedded, Product
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

inventory_bp = Blueprint('inventory', __name__)

# Supplier Routes

@inventory_bp.route('/suppliers', methods=['GET'])
@require_auth
def get_suppliers(current_user=None):
    """Get all suppliers with optional filters"""
    try:
        status = request.args.get('status')
        search = request.args.get('search')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Supplier.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if status:
            query = query.filter(status=status)
        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(contact_no__icontains=search)
            )

        suppliers = query.order_by('name')

        return jsonify([{
            'id': str(s.id),
            'name': s.name,
            'contact_no': s.contact_no,
            'email': s.email,
            'address': s.address,
            'status': s.status,
            'created_at': s.created_at.isoformat() if s.created_at else None
        } for s in suppliers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/suppliers/<id>', methods=['GET'])
@require_auth
def get_supplier(id, current_user=None):
    """Get a single supplier by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid supplier ID format'}), 400
        
        supplier = Supplier.objects.get(id=id)
        return jsonify({
            'id': str(supplier.id),
            'name': supplier.name,
            'contact_no': supplier.contact_no,
            'email': supplier.email,
            'address': supplier.address,
            'status': supplier.status,
            'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
            'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Supplier not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/suppliers', methods=['POST'])
@require_role('manager', 'owner')
def create_supplier(current_user=None):
    """Create a new supplier (Manager and Owner only)"""
    try:
        data = request.get_json()

        supplier = Supplier(
            name=data['name'],
            contact_no=data.get('contact_no'),
            email=data.get('email'),
            address=data.get('address'),
            status=data.get('status', 'active')
        )
        supplier.save()

        return jsonify({
            'id': str(supplier.id),
            'message': 'Supplier created successfully',
            'data': {
                'id': str(supplier.id),
                'name': supplier.name
            }
        }), 201
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/suppliers/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_supplier(id, current_user=None):
    """Update a supplier (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid supplier ID format'}), 400
        
        supplier = Supplier.objects.get(id=id)
        data = request.get_json()

        supplier.name = data.get('name', supplier.name)
        supplier.contact_no = data.get('contact_no', supplier.contact_no)
        supplier.email = data.get('email', supplier.email)
        supplier.address = data.get('address', supplier.address)
        supplier.status = data.get('status', supplier.status)
        supplier.updated_at = datetime.utcnow()
        supplier.save()

        return jsonify({
            'id': str(supplier.id),
            'message': 'Supplier updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Supplier not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/suppliers/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_supplier(id, current_user=None):
    """Delete a supplier (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid supplier ID format'}), 400
        
        supplier = Supplier.objects.get(id=id)

        # Check if supplier has orders
        order_count = Order.objects(supplier=supplier).count()
        if order_count > 0:
            return jsonify({'error': 'Cannot delete supplier with associated orders'}), 400

        supplier.delete()

        return jsonify({'message': 'Supplier deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Supplier not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Order Routes

@inventory_bp.route('/orders', methods=['GET'])
@require_auth
def get_orders(current_user=None):
    """Get all orders with optional filters"""
    try:
        supplier_id = request.args.get('supplier_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Order.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if supplier_id:
            if ObjectId.is_valid(supplier_id):
                query = query.filter(supplier=ObjectId(supplier_id))
        if status:
            query = query.filter(status=status)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(order_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(order_date__lte=end)

        orders = query.order_by('-order_date')

        return jsonify([{
            'id': str(o.id),
            'supplier_id': str(o.supplier.id) if o.supplier else None,
            'supplier_name': o.supplier.name if o.supplier else None,
            'order_date': o.order_date.isoformat() if o.order_date else None,
            'total_amount': o.total_amount,
            'status': o.status,
            'notes': o.notes,
            'items_count': len(o.order_items) if o.order_items else 0,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/orders/<id>', methods=['GET'])
def get_order(id):
    """Get a single order with items"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid order ID format'}), 400
        
        order = Order.objects.get(id=id)

        return jsonify({
            'id': str(order.id),
            'supplier_id': str(order.supplier.id) if order.supplier else None,
            'supplier_name': order.supplier.name if order.supplier else None,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'total_amount': order.total_amount,
            'status': order.status,
            'notes': order.notes,
            'items': [{
                'product_id': str(item.product.id) if item.product else None,
                'product_name': item.product.name if item.product else None,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total': item.total
            } for item in (order.order_items or [])],
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/orders', methods=['POST'])
@require_role('manager', 'owner')
def create_order(current_user=None):
    """Create a new order with items (Manager and Owner only)"""
    try:
        data = request.get_json()

        # Parse order date
        order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()

        # Get supplier reference
        supplier_id = data.get('supplier_id')
        if not supplier_id or not ObjectId.is_valid(supplier_id):
            return jsonify({'error': 'Invalid supplier ID format'}), 400
        
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except DoesNotExist:
            return jsonify({'error': 'Supplier not found'}), 404

        # Create order items as embedded documents
        order_items = []
        if 'items' in data:
            for item_data in data['items']:
                product_id = item_data.get('product_id')
                if not product_id or not ObjectId.is_valid(product_id):
                    return jsonify({'error': f'Invalid product ID format: {product_id}'}), 400
                
                try:
                    product = Product.objects.get(id=product_id)
                except DoesNotExist:
                    return jsonify({'error': f'Product not found: {product_id}'}), 404
                
                order_item = OrderItemEmbedded(
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=item_data.get('unit_price', 0),
                    total=item_data.get('total', item_data['quantity'] * item_data.get('unit_price', 0))
                )
                order_items.append(order_item)

        # Create order
        order = Order(
            supplier=supplier,
            order_date=order_date,
            total_amount=data.get('total_amount', sum(item.total for item in order_items)),
            status=data.get('status', 'pending'),
            notes=data.get('notes'),
            order_items=order_items
        )
        order.save()

        return jsonify({
            'id': str(order.id),
            'message': 'Order created successfully',
            'data': {
                'id': str(order.id),
                'total_amount': order.total_amount
            }
        }), 201
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/orders/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_order(id, current_user=None):
    """Update an order (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid order ID format'}), 400
        
        order = Order.objects.get(id=id)
        data = request.get_json()

        old_status = order.status

        # Update order date if provided
        if 'order_date' in data:
            order.order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()

        order.total_amount = data.get('total_amount', order.total_amount)
        order.status = data.get('status', order.status)
        order.notes = data.get('notes', order.notes)
        order.updated_at = datetime.utcnow()

        # If status changed to 'received', update product stock
        if data.get('status') == 'received' and old_status != 'received':
            for item in (order.order_items or []):
                if item.product:
                    product = Product.objects.get(id=item.product.id)
                    product.stock_quantity = (product.stock_quantity or 0) + item.quantity
                    product.updated_at = datetime.utcnow()
                    product.save()

        order.save()

        return jsonify({
            'id': str(order.id),
            'message': 'Order updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/orders/<id>/receive', methods=['POST'])
@require_role('manager', 'owner')
def receive_order(id, current_user=None):
    """Mark order as received and update product stock (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid order ID format'}), 400
        
        order = Order.objects.get(id=id)

        if order.status == 'received':
            return jsonify({'error': 'Order already received'}), 400

        # Update product stock for all items
        for item in (order.order_items or []):
            if item.product:
                product = Product.objects.get(id=item.product.id)
                product.stock_quantity = (product.stock_quantity or 0) + item.quantity
                product.updated_at = datetime.utcnow()
                product.save()

        # Update order status
        order.status = 'received'
        order.updated_at = datetime.utcnow()
        order.save()

        return jsonify({
            'message': 'Order received and stock updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/orders/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_order(id, current_user=None):
    """Delete an order (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid order ID format'}), 400
        
        order = Order.objects.get(id=id)

        if order.status == 'received':
            return jsonify({'error': 'Cannot delete received order'}), 400

        order.delete()

        return jsonify({'message': 'Order deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Inventory Reports

@inventory_bp.route('/products', methods=['GET'])
def get_inventory_products():
    """Get all products with stock information"""
    try:
        low_stock = request.args.get('low_stock', '').lower() == 'true'

        query = Product.objects.filter(status='active')
        products = list(query)

        if low_stock:
            # Filter products where stock_quantity <= min_stock_level
            products = [p for p in products if (p.stock_quantity or 0) <= (p.min_stock_level or 0)]

        # Sort by stock_quantity
        products.sort(key=lambda p: p.stock_quantity or 0)

        return jsonify([{
            'id': str(p.id),
            'name': p.name,
            'category_name': p.category.name if p.category else None,
            'stock_quantity': p.stock_quantity or 0,
            'min_stock_level': p.min_stock_level or 0,
            'price': p.price or 0,
            'cost': p.cost or 0,
            'low_stock': (p.stock_quantity or 0) <= (p.min_stock_level or 0),
            'stock_value': (p.stock_quantity or 0) * (p.cost or 0)
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get products with low stock"""
    try:
        # Get all active products and filter in Python
        all_products = list(Product.objects.filter(status='active'))
        products = [p for p in all_products if (p.stock_quantity or 0) <= (p.min_stock_level or 0)]
        # Sort by stock_quantity
        products.sort(key=lambda p: p.stock_quantity or 0)

        return jsonify([{
            'id': str(p.id),
            'name': p.name,
            'category_name': p.category.name if p.category else None,
            'stock_quantity': p.stock_quantity or 0,
            'min_stock_level': p.min_stock_level or 0,
            'deficit': max((p.min_stock_level or 0) - (p.stock_quantity or 0), 0),
            'reorder_suggested': max((p.min_stock_level or 0) * 2 - (p.stock_quantity or 0), 0)
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/summary', methods=['GET'])
def get_inventory_summary():
    """Get inventory summary"""
    try:
        products = list(Product.objects.filter(status='active'))

        total_products = len(products)
        total_stock_value = sum([(p.stock_quantity or 0) * (p.cost or 0) for p in products])
        low_stock_count = len([p for p in products if (p.stock_quantity or 0) <= (p.min_stock_level or 0)])
        out_of_stock_count = len([p for p in products if (p.stock_quantity or 0) == 0])

        return jsonify({
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_items': low_stock_count,
            'out_of_stock_items': out_of_stock_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
