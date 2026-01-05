from flask import Blueprint, request, jsonify
from models import PrepaidPackage, PrepaidGroup, Customer
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId

prepaid_bp = Blueprint('prepaid', __name__)

@prepaid_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Prepaid Group Routes

@prepaid_bp.route('/groups', methods=['GET'])
def get_prepaid_groups():
    """Get all prepaid groups"""
    try:
        # Force evaluation by converting to list
        groups = list(PrepaidGroup.objects.order_by('display_order'))
        return jsonify([{
            'id': str(g.id),
            'name': g.name,
            'display_order': g.display_order,
            'created_at': g.created_at.isoformat() if g.created_at else None
        } for g in groups])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/groups', methods=['POST'])
def create_prepaid_group():
    """Create a new prepaid group"""
    try:
        data = request.get_json()

        group = PrepaidGroup(
            name=data['name'],
            display_order=data.get('display_order', 0)
        )
        group.save()

        return jsonify({
            'id': str(group.id),
            'message': 'Prepaid group created successfully',
            'data': {
                'id': str(group.id),
                'name': group.name
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/groups/<id>', methods=['PUT'])
def update_prepaid_group(id):
    """Update a prepaid group"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid group ID format'}), 400
        
        group = PrepaidGroup.objects.get(id=id)
        data = request.get_json()

        group.name = data.get('name', group.name)
        group.display_order = data.get('display_order', group.display_order)
        group.save()

        return jsonify({
            'id': str(group.id),
            'message': 'Prepaid group updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Group not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/groups/<id>', methods=['DELETE'])
def delete_prepaid_group(id):
    """Delete a prepaid group"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid group ID format'}), 400
        
        group = PrepaidGroup.objects.get(id=id)

        # Check if group has prepaid packages
        package_count = PrepaidPackage.objects(group=group).count()
        if package_count > 0:
            return jsonify({'error': 'Cannot delete group with associated prepaid packages'}), 400

        group.delete()

        return jsonify({'message': 'Prepaid group deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Group not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Prepaid Package Routes

@prepaid_bp.route('/packages', methods=['GET'])
def get_prepaid_packages():
    """Get all prepaid packages with optional filters"""
    try:
        customer_id = request.args.get('customer_id', type=str)
        status = request.args.get('status')
        group_id = request.args.get('group_id', type=str)

        query = PrepaidPackage.objects

        # Apply filters
        if customer_id and ObjectId.is_valid(customer_id):
            try:
                customer = Customer.objects.get(id=customer_id)
                query = query.filter(customer=customer)
            except DoesNotExist:
                pass
        if status:
            query = query.filter(status=status)
        if group_id and ObjectId.is_valid(group_id):
            try:
                group = PrepaidGroup.objects.get(id=group_id)
                query = query.filter(group=group)
            except DoesNotExist:
                pass

        # Force evaluation by converting to list
        packages = list(query.order_by('-created_at'))

        return jsonify([{
            'id': str(p.id),
            'name': p.name,
            'group_id': str(p.group.id) if p.group else None,
            'group_name': p.group.name if p.group else None,
            'price': p.price,
            'customer_id': str(p.customer.id) if p.customer else None,
            'customer_name': f"{p.customer.first_name} {p.customer.last_name}" if p.customer else None,
            'customer_mobile': p.customer.mobile if p.customer else None,
            'remaining_balance': p.remaining_balance,
            'purchase_date': p.purchase_date.isoformat() if p.purchase_date else None,
            'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
            'status': p.status,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in packages])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/packages/<id>', methods=['GET'])
def get_prepaid_package(id):
    """Get a single prepaid package by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = PrepaidPackage.objects.get(id=id)
        return jsonify({
            'id': str(package.id),
            'name': package.name,
            'group_id': str(package.group.id) if package.group else None,
            'group_name': package.group.name if package.group else None,
            'price': package.price,
            'customer_id': str(package.customer.id) if package.customer else None,
            'customer_name': f"{package.customer.first_name} {package.customer.last_name}" if package.customer else None,
            'remaining_balance': package.remaining_balance,
            'purchase_date': package.purchase_date.isoformat() if package.purchase_date else None,
            'expiry_date': package.expiry_date.isoformat() if package.expiry_date else None,
            'status': package.status,
            'created_at': package.created_at.isoformat() if package.created_at else None,
            'updated_at': package.updated_at.isoformat() if package.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/packages', methods=['POST'])
def create_prepaid_package():
    """Create a new prepaid package (purchase by customer)"""
    try:
        data = request.get_json()

        # Validate customer exists
        if not ObjectId.is_valid(data['customer_id']):
            return jsonify({'error': 'Invalid customer ID format'}), 400
        
        try:
            customer = Customer.objects.get(id=data['customer_id'])
        except DoesNotExist:
            return jsonify({'error': 'Customer not found'}), 404

        # Get group reference
        group = None
        if data.get('group_id'):
            if not ObjectId.is_valid(data['group_id']):
                return jsonify({'error': 'Invalid group ID format'}), 400
            try:
                group = PrepaidGroup.objects.get(id=data['group_id'])
            except DoesNotExist:
                return jsonify({'error': 'Group not found'}), 400

        # Parse dates
        purchase_date = datetime.fromisoformat(data['purchase_date']) if 'purchase_date' in data else datetime.utcnow()
        expiry_date = datetime.fromisoformat(data['expiry_date']) if 'expiry_date' in data else None

        package = PrepaidPackage(
            name=data['name'],
            group=group,
            price=data['price'],
            customer=customer,
            remaining_balance=data.get('remaining_balance', data['price']),
            purchase_date=purchase_date,
            expiry_date=expiry_date,
            status=data.get('status', 'active')
        )
        package.save()

        return jsonify({
            'id': str(package.id),
            'message': 'Prepaid package created successfully',
            'data': {
                'id': str(package.id),
                'name': package.name,
                'price': package.price,
                'remaining_balance': package.remaining_balance
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/packages/<id>', methods=['PUT'])
def update_prepaid_package(id):
    """Update a prepaid package"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = PrepaidPackage.objects.get(id=id)
        data = request.get_json()

        package.name = data.get('name', package.name)
        
        # Update group if provided
        if 'group_id' in data:
            if data['group_id']:
                if not ObjectId.is_valid(data['group_id']):
                    return jsonify({'error': 'Invalid group ID format'}), 400
                try:
                    package.group = PrepaidGroup.objects.get(id=data['group_id'])
                except DoesNotExist:
                    return jsonify({'error': 'Group not found'}), 400
            else:
                package.group = None
        
        package.price = data.get('price', package.price)
        package.remaining_balance = data.get('remaining_balance', package.remaining_balance)

        # Update dates if provided
        if 'purchase_date' in data:
            package.purchase_date = datetime.fromisoformat(data['purchase_date'])
        if 'expiry_date' in data:
            package.expiry_date = datetime.fromisoformat(data['expiry_date'])

        package.status = data.get('status', package.status)
        package.updated_at = datetime.utcnow()
        package.save()

        return jsonify({
            'id': str(package.id),
            'message': 'Prepaid package updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/packages/<id>', methods=['DELETE'])
def delete_prepaid_package(id):
    """Delete a prepaid package"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = PrepaidPackage.objects.get(id=id)
        package.delete()

        return jsonify({'message': 'Prepaid package deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/clients', methods=['GET'])
def get_prepaid_clients():
    """Get all clients with active prepaid packages"""
    try:
        # Get all active prepaid packages - force evaluation
        active_packages = list(PrepaidPackage.objects(status='active'))

        # Group by customer
        client_data = {}
        for package in active_packages:
            if package.customer:
                customer_id = str(package.customer.id)
                if customer_id not in client_data:
                    customer = package.customer
                    client_data[customer_id] = {
                        'customer_id': str(customer.id),
                        'customer_name': f"{customer.first_name} {customer.last_name}",
                        'mobile': customer.mobile,
                        'packages': []
                    }

                client_data[customer_id]['packages'].append({
                    'id': str(package.id),
                    'name': package.name,
                    'remaining_balance': package.remaining_balance,
                    'expiry_date': package.expiry_date.isoformat() if package.expiry_date else None
                })

        return jsonify(list(client_data.values()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prepaid_bp.route('/packages/<id>/use', methods=['POST'])
def use_prepaid_balance(id):
    """Use/deduct from prepaid package balance"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid package ID format'}), 400
        
        package = PrepaidPackage.objects.get(id=id)
        data = request.get_json()

        amount = data.get('amount', 0)

        if amount > package.remaining_balance:
            return jsonify({'error': 'Insufficient prepaid balance'}), 400

        package.remaining_balance -= amount

        # Update status if balance is exhausted
        if package.remaining_balance <= 0:
            package.status = 'used'

        package.updated_at = datetime.utcnow()
        package.save()

        return jsonify({
            'message': 'Prepaid balance updated successfully',
            'remaining_balance': package.remaining_balance
        })
    except DoesNotExist:
        return jsonify({'error': 'Package not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
