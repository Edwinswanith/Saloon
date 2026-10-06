from flask import Blueprint, request, jsonify
from models import Supplier, Order, OrderItemEmbedded, Product, ProductConsumptionLog
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.auth import require_auth, require_role
from utils.branch_filter import apply_branch_scope, get_selected_branch

inventory_bp = Blueprint('inventory', __name__)


def _current_user_name(current_user):
    if not current_user:
        return None
    if isinstance(current_user, dict):
        return current_user.get('name') or current_user.get('email') or current_user.get('mobile')
    return getattr(current_user, 'name', None) or getattr(current_user, 'email', None) or getattr(current_user, 'mobile', None)


def _parse_quantity(value):
    try:
        quantity = float(value)
    except (TypeError, ValueError):
        raise ValueError('Quantity must be a valid number')

    if quantity <= 0:
        raise ValueError('Quantity must be greater than zero')
    return round(quantity, 3)


def _stock_unit(product=None, fallback=None):
    unit = fallback or getattr(product, 'stock_unit', None) or 'units'
    unit = str(unit).strip()
    return unit[:20] if unit else 'units'


def _round_stock(value):
    return round(float(value or 0), 3)


def _serialize_consumption_log(log):
    product = log.product if log.product else None
    unit = _stock_unit(product, getattr(log, 'unit', None))
    return {
        'id': str(log.id),
        'product_id': str(product.id) if product else None,
        'product_name': product.name if product else 'Deleted Product',
        'quantity': log.quantity or 0,
        'unit': unit,
        'consumption_date': log.consumption_date.isoformat() if log.consumption_date else None,
        'service_name': log.service_name,
        'period_label': log.period_label,
        'reason': log.reason,
        'consumption_type': log.consumption_type,
        'created_by_name': log.created_by_name,
        'created_at': log.created_at.isoformat() if log.created_at else None,
        'updated_at': log.updated_at.isoformat() if getattr(log, 'updated_at', None) else None,
    }

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
        query = apply_branch_scope(query, branch, current_user)

        # Apply filters
        if status:
            query = query.filter(status=status)
        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(contact_no__icontains=search)
            )

        # Force evaluation by converting to list
        suppliers = list(query.order_by('name'))

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
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        supplier = Supplier(
            name=data['name'],
            contact_no=data.get('contact_no'),
            email=data.get('email'),
            address=data.get('address'),
            status=data.get('status', 'active'),
            branch=branch
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
        query = apply_branch_scope(query, branch, current_user)

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
            # Note: order_date is a DateField, so we can't set time, but the filter will include the full day
            query = query.filter(order_date__lte=end)

        # Force evaluation by converting to list
        orders = list(query.order_by('-order_date'))

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
@require_auth
def get_order(id, current_user=None):
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
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

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

        if supplier.branch and str(supplier.branch.id) != str(branch.id):
            return jsonify({'error': 'Supplier belongs to a different branch'}), 400

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
                if product.branch and str(product.branch.id) != str(branch.id):
                    return jsonify({'error': f'Product belongs to a different branch: {product.name}'}), 400
                
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
            branch=branch,
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

        # If status changed to 'received', update product stock atomically.
        # Use $inc via update_one so concurrent receives don't race on a load-modify-save.
        # Also skip (rather than 500) if the product was deleted between create and receive.
        if data.get('status') == 'received' and old_status != 'received':
            for item in (order.order_items or []):
                if not item.product:
                    continue
                try:
                    Product.objects(id=item.product.id).update_one(
                        inc__stock_quantity=int(item.quantity or 0),
                        set__updated_at=datetime.utcnow()
                    )
                except DoesNotExist:
                    print(f"[INVENTORY] Product {item.product.id} no longer exists — stock not updated for order {order.id}")
                except Exception as stock_err:
                    print(f"[INVENTORY] Stock update failed for product {item.product.id}: {stock_err}")

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
@require_auth
def get_inventory_products(current_user=None):
    """Get all products with stock information, filtered by branch"""
    try:
        low_stock = request.args.get('low_stock', '').lower() == 'true'

        query = Product.objects.filter(status='active')

        # Filter by branch - strict filtering
        branch = get_selected_branch(request, current_user)
        query = apply_branch_scope(query, branch, current_user)

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
            'stock_unit': p.stock_unit or 'units',
            'price': p.price or 0,
            'cost': p.cost or 0,
            'low_stock': (p.stock_quantity or 0) <= (p.min_stock_level or 0),
            'stock_value': (p.stock_quantity or 0) * (p.cost or 0)
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
@require_auth
def get_low_stock_items(current_user=None):
    """Get products with low stock, filtered by branch"""
    try:
        query = Product.objects.filter(status='active')

        # Filter by branch - strict filtering
        branch = get_selected_branch(request, current_user)
        query = apply_branch_scope(query, branch, current_user)

        # Get all active products and filter in Python
        all_products = list(query)
        products = [p for p in all_products if (p.stock_quantity or 0) <= (p.min_stock_level or 0)]
        # Sort by stock_quantity
        products.sort(key=lambda p: p.stock_quantity or 0)

        return jsonify([{
            'id': str(p.id),
            'name': p.name,
            'category_name': p.category.name if p.category else None,
            'stock_quantity': p.stock_quantity or 0,
            'min_stock_level': p.min_stock_level or 0,
            'stock_unit': p.stock_unit or 'units',
            'deficit': max((p.min_stock_level or 0) - (p.stock_quantity or 0), 0),
            'reorder_suggested': max((p.min_stock_level or 0) * 2 - (p.stock_quantity or 0), 0)
        } for p in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/summary', methods=['GET'])
@require_auth
def get_inventory_summary(current_user=None):
    """Get inventory summary, filtered by branch"""
    try:
        query = Product.objects.filter(status='active')

        # Filter by branch - strict filtering
        branch = get_selected_branch(request, current_user)
        query = apply_branch_scope(query, branch, current_user)

        products = list(query)

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


@inventory_bp.route('/consumption', methods=['GET'])
@require_auth
def get_consumption_logs(current_user=None):
    """Get product consumption logs for the selected branch."""
    try:
        branch = get_selected_branch(request, current_user)
        query = ProductConsumptionLog.objects
        query = apply_branch_scope(query, branch, current_user)

        product_id = request.args.get('product_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if product_id and ObjectId.is_valid(product_id):
            query = query.filter(product=ObjectId(product_id))
        if start_date:
            query = query.filter(consumption_date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(consumption_date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())

        logs = list(query.order_by('-consumption_date', '-created_at').limit(200))

        return jsonify([_serialize_consumption_log(log) for log in logs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/consumption', methods=['POST'])
@require_role('staff', 'manager', 'owner')
def create_consumption_log(current_user=None):
    """Record product consumption and decrement stock."""
    try:
        data = request.get_json() or {}
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        product_id = data.get('product_id')
        if not product_id or not ObjectId.is_valid(product_id):
            return jsonify({'error': 'Valid product_id is required'}), 400

        try:
            product = Product.objects.get(id=product_id)
        except DoesNotExist:
            return jsonify({'error': 'Product not found'}), 404

        if product.branch and str(product.branch.id) != str(branch.id):
            return jsonify({'error': 'Product belongs to a different branch'}), 400

        quantity = _parse_quantity(data.get('quantity'))

        available_stock = _round_stock(product.stock_quantity)
        if available_stock < quantity:
            return jsonify({
                'error': f'Insufficient stock. Available: {available_stock} {_stock_unit(product)}, Required: {quantity} {_stock_unit(product)}'
            }), 400

        consumption_date = datetime.strptime(
            data.get('consumption_date') or datetime.utcnow().strftime('%Y-%m-%d'),
            '%Y-%m-%d'
        ).date()

        product.stock_quantity = _round_stock(available_stock - quantity)
        product.updated_at = datetime.utcnow()
        product.save()

        log = ProductConsumptionLog(
            product=product,
            branch=branch,
            quantity=quantity,
            unit=_stock_unit(product),
            consumption_date=consumption_date,
            service_name=data.get('service_name') or '',
            period_label=data.get('period_label') or '',
            reason=data.get('reason') or '',
            consumption_type=data.get('consumption_type') or 'manual',
            created_by_name=_current_user_name(current_user)
        )
        log.save()

        return jsonify({
            'id': str(log.id),
            'message': 'Product consumption recorded successfully',
            'remaining_stock': product.stock_quantity,
            'unit': _stock_unit(product)
        }), 201
    except ValueError as e:
        return jsonify({'error': f'Invalid value: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/consumption/<id>', methods=['PUT'])
@require_role('staff', 'manager', 'owner')
def update_consumption_log(id, current_user=None):
    """Update product consumption and adjust stock by the changed quantity."""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid consumption ID format'}), 400

        data = request.get_json() or {}
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        query = ProductConsumptionLog.objects
        query = apply_branch_scope(query, branch, current_user)
        try:
            log = query.get(id=id)
        except DoesNotExist:
            return jsonify({'error': 'Consumption record not found'}), 404

        product_id = data.get('product_id') or (str(log.product.id) if log.product else None)
        if not product_id or not ObjectId.is_valid(product_id):
            return jsonify({'error': 'Valid product_id is required'}), 400

        try:
            new_product = Product.objects.get(id=product_id)
        except DoesNotExist:
            return jsonify({'error': 'Product not found'}), 404

        if new_product.branch and str(new_product.branch.id) != str(branch.id):
            return jsonify({'error': 'Product belongs to a different branch'}), 400

        new_quantity = _parse_quantity(data.get('quantity'))
        old_quantity = _round_stock(log.quantity)
        old_product = log.product
        same_product = old_product and str(old_product.id) == str(new_product.id)

        if same_product:
            available_stock = _round_stock(new_product.stock_quantity)
            additional_required = _round_stock(new_quantity - old_quantity)
            if additional_required > 0 and available_stock < additional_required:
                return jsonify({
                    'error': (
                        f'Insufficient stock. Available: {available_stock} {_stock_unit(new_product)}, '
                        f'Required extra: {additional_required} {_stock_unit(new_product)}'
                    )
                }), 400

            new_product.stock_quantity = _round_stock(available_stock - additional_required)
            new_product.updated_at = datetime.utcnow()
            new_product.save()
        else:
            available_stock = _round_stock(new_product.stock_quantity)
            if available_stock < new_quantity:
                return jsonify({
                    'error': f'Insufficient stock. Available: {available_stock} {_stock_unit(new_product)}, Required: {new_quantity} {_stock_unit(new_product)}'
                }), 400

            if old_product:
                old_product.reload()
                if not old_product.branch or str(old_product.branch.id) == str(branch.id):
                    old_product.stock_quantity = _round_stock((old_product.stock_quantity or 0) + old_quantity)
                    old_product.updated_at = datetime.utcnow()
                    old_product.save()

            new_product.reload()
            new_product.stock_quantity = _round_stock((new_product.stock_quantity or 0) - new_quantity)
            new_product.updated_at = datetime.utcnow()
            new_product.save()

        if data.get('consumption_date'):
            log.consumption_date = datetime.strptime(data.get('consumption_date'), '%Y-%m-%d').date()
        log.product = new_product
        log.branch = branch
        log.quantity = new_quantity
        log.unit = _stock_unit(new_product)
        log.service_name = data.get('service_name') if data.get('service_name') is not None else log.service_name
        log.period_label = data.get('period_label') if data.get('period_label') is not None else log.period_label
        log.reason = data.get('reason') if data.get('reason') is not None else log.reason
        log.consumption_type = data.get('consumption_type') or log.consumption_type or 'service'
        log.updated_at = datetime.utcnow()
        log.save()

        return jsonify({
            'message': 'Product consumption updated successfully',
            'remaining_stock': new_product.stock_quantity,
            'unit': _stock_unit(new_product),
            'data': _serialize_consumption_log(log)
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/consumption-summary', methods=['GET'])
@require_auth
def get_consumption_summary(current_user=None):
    """Summarize product consumption for the selected period."""
    try:
        branch = get_selected_branch(request, current_user)
        end_date = request.args.get('end_date')
        start_date = request.args.get('start_date')

        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = datetime.utcnow().date()
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start = end - timedelta(days=30)

        match = {
            'consumption_date': {'$gte': start, '$lte': end}
        }
        if branch:
            match['branch'] = ObjectId(str(branch.id))

        pipeline = [
            {'$match': match},
            {'$group': {
                '_id': '$product',
                'total_quantity': {'$sum': {'$ifNull': ['$quantity', 0]}},
                'last_consumed': {'$max': '$consumption_date'},
                'service_names': {'$addToSet': '$service_name'}
            }},
            {'$sort': {'total_quantity': -1}},
            {'$limit': 25}
        ]
        rows = list(ProductConsumptionLog.objects.aggregate(pipeline))
        product_ids = [row['_id'] for row in rows if row.get('_id')]
        product_map = {p.id: p for p in Product.objects(id__in=product_ids)} if product_ids else {}

        return jsonify({
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'items': [{
                'product_id': str(row.get('_id')) if row.get('_id') else None,
                'product_name': product_map.get(row.get('_id')).name if product_map.get(row.get('_id')) else 'Deleted Product',
                'total_quantity': row.get('total_quantity', 0),
                'unit': _stock_unit(product_map.get(row.get('_id'))),
                'last_consumed': row.get('last_consumed').isoformat() if row.get('last_consumed') else None,
                'service_names': [name for name in row.get('service_names', []) if name],
            } for row in rows]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
