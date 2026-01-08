from flask import Blueprint, request, jsonify
from models import Customer, Bill, Membership
from datetime import datetime
from mongoengine import Q
from utils.auth import require_auth
from utils.branch_filter import get_selected_branch, filter_by_branch
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
@require_auth
def get_customers(current_user=None):
    """Get all customers with optional search"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get branch for filtering
    branch = get_selected_branch(request, current_user)
    query = Customer.objects
    if branch:
        query = query.filter(branch=branch)
    
    if search:
        query = query.filter(
            Q(mobile__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    total = query.count()
    # Force evaluation by converting to list
    customers = list(query.skip((page - 1) * per_page).limit(per_page))
    
    return jsonify({
        'customers': [{
            'id': str(c.id),
            'mobile': c.mobile,
            'firstName': c.first_name,
            'lastName': c.last_name,
            'source': c.source,
            'gender': c.gender,
            'dobRange': c.dob_range,
            'referralCode': c.referral_code
        } for c in customers],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@customer_bp.route('/<customer_id>', methods=['GET'])
@require_auth
def get_customer(customer_id, current_user=None):
    """Get single customer by ID with visit history"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        if branch:
            query = query.filter(branch=branch)
        customer = query.first()
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # Calculate visit history and revenue from bills
        bills_query = Bill.objects(customer=customer)
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        bills = list(bills_query)
        total_visits = len(bills)
        total_revenue = sum(bill.final_amount for bill in bills if bill.final_amount)
        last_visit = max((bill.bill_date for bill in bills if bill.bill_date), default=None)
        
        # Get active membership info
        active_membership = Membership.objects(
            customer=customer,
            status='active',
            expiry_date__gte=datetime.utcnow()
        ).first()
        
        membership_data = None
        if active_membership:
            membership_data = {
                'id': str(active_membership.id),
                'name': active_membership.name,
                'plan': {
                    'id': str(active_membership.plan.id) if active_membership.plan else None,
                    'name': active_membership.plan.name if active_membership.plan else None,
                    'allocated_discount': active_membership.plan.allocated_discount if active_membership.plan else 0.0
                } if active_membership.plan else None,
                'purchase_date': active_membership.purchase_date.isoformat() if active_membership.purchase_date else None,
                'expiry_date': active_membership.expiry_date.isoformat() if active_membership.expiry_date else None,
                'status': active_membership.status
            }
        
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
            'referralCode': customer.referral_code,
            'membership': membership_data,
            'last_visit': last_visit.isoformat() if last_visit else None,
            'total_visits': total_visits,
            'total_revenue': total_revenue,
            'notes': getattr(customer, 'notes', 'N/A')
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        print(f"Error fetching customer details: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/', methods=['POST'])
@require_auth
def create_customer(current_user=None):
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
        
        # Get branch for assignment
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check if mobile already exists in this branch
        existing = Customer.objects(mobile=data.get('mobile'), branch=branch).first()
        if existing:
            response = jsonify({'error': 'Customer with this mobile number already exists in this branch'})
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
            referral_code=generate_referral_code(data.get('firstName', '')),
            branch=branch
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
@require_auth
def update_customer(customer_id, current_user=None):
    """Update customer"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        if branch:
            query = query.filter(branch=branch)
        customer = query.first()
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
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

@customer_bp.route('/<customer_id>/active-membership', methods=['GET'])
@require_auth
def get_customer_active_membership(customer_id, current_user=None):
    """Get customer's active membership with plan details"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        if branch:
            query = query.filter(branch=branch)
        customer = query.first()
        
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # Get active membership (status='active' and expiry_date >= today)
        membership_query = Membership.objects(
            customer=customer,
            status='active',
            expiry_date__gte=datetime.utcnow()
        )
        if branch:
            membership_query = membership_query.filter(branch=branch)
        
        active_membership = membership_query.first()
        
        if not active_membership:
            response = jsonify({
                'active': False,
                'membership': None
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        
        # Return membership with plan details
        membership_data = {
            'id': str(active_membership.id),
            'name': active_membership.name,
            'purchase_date': active_membership.purchase_date.isoformat() if active_membership.purchase_date else None,
            'expiry_date': active_membership.expiry_date.isoformat() if active_membership.expiry_date else None,
            'status': active_membership.status,
            'plan': None
        }
        
        if active_membership.plan:
            membership_data['plan'] = {
                'id': str(active_membership.plan.id),
                'name': active_membership.plan.name,
                'allocated_discount': active_membership.plan.allocated_discount,
                'validity_days': active_membership.plan.validity_days,
                'description': active_membership.plan.description
            }
        
        response = jsonify({
            'active': True,
            'membership': membership_data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        print(f"Error fetching customer active membership: {str(e)}")
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
            'lastName': c.last_name
        } for c in customers]
    })
