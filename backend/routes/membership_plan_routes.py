from flask import Blueprint, request, jsonify
from models import MembershipPlan, Membership
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_role

membership_plan_bp = Blueprint('membership_plans', __name__)

@membership_plan_bp.route('/', methods=['GET'])
def get_membership_plans():
    """Get all membership plans"""
    try:
        status = request.args.get('status', 'all')
        
        query = MembershipPlan.objects
        
        if status != 'all':
            query = query.filter(status=status)

        plans = list(query.order_by('-created_at'))

        result = [{
                'id': str(p.id),
                'name': p.name,
                'validity_days': p.validity_days,
                'validity': p.validity_days,  # Keep both for compatibility
                'price': p.price,
                'allocatedDiscount': p.allocated_discount,
                'allocated_discount': p.allocated_discount,  # Keep both for compatibility
                'status': p.status,
                'description': p.description
            } for p in plans]
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@membership_plan_bp.route('/<plan_id>', methods=['GET'])
def get_membership_plan(plan_id):
    """Get single membership plan"""
    try:
        if not ObjectId.is_valid(plan_id):
            return jsonify({'error': 'Invalid plan ID format'}), 400
        
        plan = MembershipPlan.objects.get(id=plan_id)
        response = jsonify({
            'id': str(plan.id),
            'name': plan.name,
            'validity': plan.validity_days,
            'price': plan.price,
            'allocatedDiscount': plan.allocated_discount,
            'status': plan.status,
            'description': plan.description
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Plan not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@membership_plan_bp.route('/', methods=['POST'])
@require_role('owner')
def create_membership_plan(current_user=None):
    """Create new membership plan (Owner only)"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('validity'):
            return jsonify({'error': 'Validity is required'}), 400
        if data.get('price') is None:
            return jsonify({'error': 'Price is required'}), 400
        
        plan = MembershipPlan(
            name=data.get('name'),
            validity_days=data.get('validity'),
            price=data.get('price'),
            allocated_discount=data.get('allocatedDiscount', 0.0),
            status=data.get('status', 'active'),
            description=data.get('description', '')
        )
        plan.save()
        
        response = jsonify({
            'id': str(plan.id),
            'message': 'Membership plan created successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@membership_plan_bp.route('/<plan_id>', methods=['PUT'])
@require_role('owner')
def update_membership_plan(plan_id, current_user=None):
    """Update membership plan (Owner only)"""
    try:
        if not ObjectId.is_valid(plan_id):
            return jsonify({'error': 'Invalid plan ID format'}), 400
        
        plan = MembershipPlan.objects.get(id=plan_id)
        data = request.json
        
        if data.get('name'):
            plan.name = data['name']
        if data.get('validity') is not None:
            plan.validity_days = data['validity']
        if data.get('price') is not None:
            plan.price = data['price']
        if data.get('allocatedDiscount') is not None:
            plan.allocated_discount = data['allocatedDiscount']
        if data.get('status'):
            plan.status = data['status']
        if data.get('description') is not None:
            plan.description = data['description']
        
        plan.updated_at = datetime.utcnow()
        plan.save()
        
        response = jsonify({'message': 'Membership plan updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Plan not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@membership_plan_bp.route('/<plan_id>', methods=['DELETE'])
@require_role('owner')
def delete_membership_plan(plan_id, current_user=None):
    """Delete membership plan (Owner only - soft delete by setting status to inactive)"""
    try:
        if not ObjectId.is_valid(plan_id):
            return jsonify({'error': 'Invalid plan ID format'}), 400
        
        plan = MembershipPlan.objects.get(id=plan_id)
        
        # Check if plan is being used by any memberships
        membership_count = Membership.objects(plan=plan).count()
        if membership_count > 0:
            # Soft delete - set status to inactive
            plan.status = 'inactive'
            plan.updated_at = datetime.utcnow()
            plan.save()
            response = jsonify({'message': 'Membership plan deactivated successfully'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            # Hard delete if not in use
            plan.delete()
            response = jsonify({'message': 'Membership plan deleted successfully'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
    except DoesNotExist:
        response = jsonify({'error': 'Plan not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

