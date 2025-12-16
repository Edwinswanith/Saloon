from flask import Blueprint, request, jsonify
from models import Customer
from datetime import datetime
from mongoengine import Q
import random
import string

customer_bp = Blueprint('customers', __name__)

@customer_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

def generate_referral_code(first_name):
    """Generate referral code from customer name"""
    name_part = first_name.upper()[:5] if first_name else 'CUST'
    random_part = ''.join(random.choices(string.digits, k=3))
    return f"{name_part}{random_part}"

@customer_bp.route('/', methods=['GET'])
def get_customers():
    """Get all customers with optional search"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Customer.objects
    
    if search:
        query = query.filter(
            Q(mobile__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    total = query.count()
    customers = query.skip((page - 1) * per_page).limit(per_page)
    
    return jsonify({
        'customers': [{
            'id': str(c.id),
            'mobile': c.mobile,
            'firstName': c.first_name,
            'lastName': c.last_name,
            'source': c.source,
            'gender': c.gender,
            'dobRange': c.dob_range,
            'loyaltyPoints': c.loyalty_points,
            'referralCode': c.referral_code,
            'wallet': c.wallet_balance
        } for c in customers],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@customer_bp.route('/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get single customer by ID"""
    try:
        customer = Customer.objects.get(id=customer_id)
        response = jsonify({
            'id': str(customer.id),
            'mobile': customer.mobile,
            'firstName': customer.first_name,
            'lastName': customer.last_name,
            'email': customer.email,
            'source': customer.source,
            'gender': customer.gender,
            'dob': customer.dob.isoformat() if customer.dob else None,
            'dobRange': customer.dob_range,
            'loyaltyPoints': customer.loyalty_points,
            'referralCode': customer.referral_code,
            'wallet': customer.wallet_balance
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

@customer_bp.route('/', methods=['POST'])
def create_customer():
    """Create new customer"""
    try:
        data = request.json
        
        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate required fields
        if not data.get('mobile'):
            response = jsonify({'error': 'Mobile number is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        if not data.get('firstName'):
            response = jsonify({'error': 'First name is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check if mobile already exists
        if Customer.objects(mobile=data.get('mobile')).first():
            response = jsonify({'error': 'Customer with this mobile number already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Handle DOB if provided
        dob = None
        if data.get('dob'):
            try:
                dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            except ValueError:
                response = jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
        
        customer = Customer(
            mobile=data.get('mobile'),
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('email', ''),
            source=data.get('source', 'Walk-in'),
            gender=data.get('gender', ''),
            dob=dob,
            dob_range=data.get('dobRange', ''),
            loyalty_points=data.get('loyaltyPoints', 0),
            wallet_balance=data.get('wallet', 0.0),
            referral_code=generate_referral_code(data.get('firstName', ''))
        )
        customer.save()
        
        response = jsonify({'id': str(customer.id), 'message': 'Customer created successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        data = request.json
        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if 'firstName' in data:
            customer.first_name = data['firstName']
        if 'lastName' in data:
            customer.last_name = data['lastName']
        if 'email' in data:
            customer.email = data['email']
        if 'source' in data:
            customer.source = data['source']
        if 'gender' in data:
            customer.gender = data['gender']
        if 'dobRange' in data:
            customer.dob_range = data['dobRange']
        if 'loyaltyPoints' in data:
            customer.loyalty_points = data['loyaltyPoints']
        if 'wallet' in data:
            customer.wallet_balance = data['wallet']
        customer.updated_at = datetime.utcnow()
        
        if data.get('dob'):
            try:
                customer.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            except ValueError:
                response = jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
        
        customer.save()
        response = jsonify({'message': 'Customer updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        customer.delete()
        response = jsonify({'message': 'Customer deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/search', methods=['GET'])
def search_customers():
    """Search customers by mobile or name (min 3 chars)"""
    query = request.args.get('q', '')
    
    if len(query) < 3:
        return jsonify({'customers': []})
    
    customers = Customer.objects.filter(
        Q(mobile__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).limit(10)
    
    return jsonify({
        'customers': [{
            'id': str(c.id),
            'mobile': c.mobile,
            'firstName': c.first_name,
            'lastName': c.last_name,
            'wallet': c.wallet_balance
        } for c in customers]
    })
