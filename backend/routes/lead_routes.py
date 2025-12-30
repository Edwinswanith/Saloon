from flask import Blueprint, request, jsonify
from models import Lead, Customer
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError
from mongoengine import Q
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth

lead_bp = Blueprint('lead', __name__)

@lead_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@lead_bp.route('/', methods=['GET'])
@require_auth
def get_leads(current_user=None):
    """Get all leads with optional filters"""
    try:
        # Query parameters
        status = request.args.get('status')
        source = request.args.get('source')
        search = request.args.get('search')
        converted = request.args.get('converted', type=bool)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Lead.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if status:
            query = query.filter(status=status)
        if source:
            query = query.filter(source=source)
        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search)
            )
        if converted is not None:
            query = query.filter(converted_to_customer=converted)

        leads = query.order_by('-created_at')

        response = jsonify([{
            'id': str(lead.id),
            'name': lead.name,
            'mobile': lead.mobile,
            'email': lead.email,
            'source': lead.source,
            'status': lead.status,
            'notes': lead.notes,
            'follow_up_date': lead.follow_up_date.isoformat() if lead.follow_up_date else None,
            'converted_to_customer': lead.converted_to_customer,
            'customer_id': str(lead.customer.id) if lead.customer else None,
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
        } for lead in leads])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/<id>', methods=['GET'])
def get_lead(id):
    """Get a single lead by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid lead ID format'}), 400
        
        lead = Lead.objects.get(id=id)
        response = jsonify({
            'id': str(lead.id),
            'name': lead.name,
            'mobile': lead.mobile,
            'email': lead.email,
            'source': lead.source,
            'status': lead.status,
            'notes': lead.notes,
            'follow_up_date': lead.follow_up_date.isoformat() if lead.follow_up_date else None,
            'converted_to_customer': lead.converted_to_customer,
            'customer_id': str(lead.customer.id) if lead.customer else None,
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/', methods=['POST'])
@require_auth
def create_lead(current_user=None):
    """Create a new lead"""
    try:
        data = request.get_json()

        # Get branch for assignment
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Parse follow-up date if provided
        follow_up_date = None
        if 'follow_up_date' in data and data['follow_up_date']:
            follow_up_date = datetime.fromisoformat(data['follow_up_date'])

        lead = Lead(
            name=data['name'],
            mobile=data.get('mobile'),
            email=data.get('email'),
            source=data.get('source'),
            status=data.get('status', 'new'),
            notes=data.get('notes'),
            follow_up_date=follow_up_date,
            branch=branch
        )
        lead.save()

        response = jsonify({
            'id': str(lead.id),
            'message': 'Lead created successfully',
            'data': {
                'id': str(lead.id),
                'name': lead.name,
                'mobile': lead.mobile
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/<id>', methods=['PUT'])
def update_lead(id):
    """Update a lead"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid lead ID format'}), 400
        
        lead = Lead.objects.get(id=id)
        data = request.get_json()

        lead.name = data.get('name', lead.name)
        lead.mobile = data.get('mobile', lead.mobile)
        lead.email = data.get('email', lead.email)
        lead.source = data.get('source', lead.source)
        lead.status = data.get('status', lead.status)
        lead.notes = data.get('notes', lead.notes)

        # Update follow-up date if provided
        if 'follow_up_date' in data:
            if data['follow_up_date']:
                lead.follow_up_date = datetime.fromisoformat(data['follow_up_date'])
            else:
                lead.follow_up_date = None

        lead.updated_at = datetime.utcnow()
        lead.save()

        response = jsonify({
            'id': str(lead.id),
            'message': 'Lead updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/<id>', methods=['DELETE'])
def delete_lead(id):
    """Delete a lead"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid lead ID format'}), 400
        
        lead = Lead.objects.get(id=id)
        lead.delete()

        response = jsonify({'message': 'Lead deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/<id>/convert', methods=['POST'])
def convert_lead_to_customer(id):
    """Convert a lead to a customer"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid lead ID format'}), 400
        
        lead = Lead.objects.get(id=id)

        if lead.converted_to_customer:
            response = jsonify({'error': 'Lead already converted to customer'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Check if customer with this mobile already exists
        if lead.mobile:
            existing_customer = Customer.objects(mobile=lead.mobile).first()
            if existing_customer:
                # Link to existing customer
                lead.customer = existing_customer
                lead.converted_to_customer = True
                lead.status = 'completed'
                lead.updated_at = datetime.utcnow()
                lead.save()

                response = jsonify({
                    'message': 'Lead linked to existing customer',
                    'customer_id': str(existing_customer.id)
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

        # Create new customer
        # Extract first and last name
        name_parts = lead.name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        customer = Customer(
            mobile=lead.mobile or '',
            first_name=first_name,
            last_name=last_name,
            email=lead.email,
            source=lead.source,
            branch=lead.branch  # Assign same branch as lead
        )
        customer.save()

        # Update lead
        lead.customer = customer
        lead.converted_to_customer = True
        lead.status = 'completed'
        lead.updated_at = datetime.utcnow()
        lead.save()

        response = jsonify({
            'message': 'Lead converted to customer successfully',
            'customer_id': str(customer.id)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@lead_bp.route('/stats', methods=['GET'])
@require_auth
def get_lead_stats(current_user=None):
    """Get lead statistics"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Lead.objects
        if branch:
            query = query.filter(branch=branch)
        # Get all leads
        all_leads = list(query)
        
        # Count leads by status
        status_counts = {}
        for lead in all_leads:
            status = lead.status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1

        # Total leads
        total = len(all_leads)

        # Converted leads
        converted = len([l for l in all_leads if l.converted_to_customer])

        # Conversion rate
        conversion_rate = (converted / total * 100) if total > 0 else 0

        response = jsonify({
            'total': total,
            'converted': converted,
            'conversion_rate': round(conversion_rate, 2),
            'by_status': status_counts
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
