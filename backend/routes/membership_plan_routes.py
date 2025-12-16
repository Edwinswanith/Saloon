from flask import Blueprint, request, jsonify
from models import MembershipPlan, Membership
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId

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

        return jsonify([{
                'id': str(p.id),
                'name': p.name,
                'validity_days': p.validity_days,
                'validity': p.validity_days,  # Keep both for compatibility
                'price': p.price,
                'allocatedDiscount': p.allocated_discount,
                'allocated_discount': p.allocated_discount,  # Keep both for compatibility
                'status': p.status,
                'description': p.description
            } for p in plans])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@membership_plan_bp.route('/<plan_id>', methods=['GET'])
def get_membership_plan(plan_id):
    """Get single membership plan"""
    try:
        if not ObjectId.is_valid(plan_id):
            return jsonify({'error': 'Invalid plan ID format'}), 400
        
        plan = MembershipPlan.objects.get(id=plan_id)
        return jsonify({
            'id': str(plan.id),
            'name': plan.name,
            'validity': plan.validity_days,
            'price': plan.price,
            'allocatedDiscount': plan.allocated_discount,
            'status': plan.status,
            'description': plan.description
        })
    except DoesNotExist:
        return jsonify({'error': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@membership_plan_bp.route('/', methods=['POST'])
def create_membership_plan():
    """Create new membership plan"""
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
        
        return jsonify({
            'id': str(plan.id),
            'message': 'Membership plan created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@membership_plan_bp.route('/<plan_id>', methods=['PUT'])
def update_membership_plan(plan_id):
    """Update membership plan"""
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
        
        return jsonify({'message': 'Membership plan updated successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@membership_plan_bp.route('/<plan_id>', methods=['DELETE'])
def delete_membership_plan(plan_id):
    """Delete membership plan (soft delete by setting status to inactive)"""
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
            return jsonify({'message': 'Membership plan deactivated successfully'})
        else:
            # Hard delete if not in use
            plan.delete()
            return jsonify({'message': 'Membership plan deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

