from flask import Blueprint, request, jsonify
from models import Staff
from datetime import datetime
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
from bson import ObjectId

staff_bp = Blueprint('staffs', __name__)

@staff_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@staff_bp.route('/', methods=['GET'])
def get_staffs():
    """Get all staff members"""
    try:
        staffs = Staff.objects(status='active')
        
        response = jsonify({
            'staffs': [{
                'id': str(s.id),
                'mobile': s.mobile,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
                'salary': s.salary,
                'commissionRate': s.commission_rate
            } for s in staffs]
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['GET'])
def get_staff(staff_id):
    """Get single staff member"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        response = jsonify({
            'id': str(staff.id),
            'mobile': staff.mobile,
            'firstName': staff.first_name,
            'lastName': staff.last_name,
            'email': staff.email,
            'salary': staff.salary,
            'commissionRate': staff.commission_rate,
            'status': staff.status
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/', methods=['POST'])
def create_staff():
    """Create new staff member"""
    try:
        data = request.get_json()
        
        if Staff.objects(mobile=data.get('mobile')).first():
            response = jsonify({'error': 'Staff with this mobile number already exists'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        staff = Staff(
            mobile=data.get('mobile'),
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('email', ''),
            salary=data.get('salary'),
            commission_rate=data.get('commissionRate', 0.0),
            status=data.get('status', 'active')
        )
        staff.save()
        
        response = jsonify({'id': str(staff.id), 'message': 'Staff created successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except NotUniqueError:
        response = jsonify({'error': 'Staff with this mobile number already exists'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['PUT'])
def update_staff(staff_id):
    """Update staff member"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        data = request.get_json()
        
        staff.first_name = data.get('firstName', staff.first_name)
        staff.last_name = data.get('lastName', staff.last_name)
        staff.email = data.get('email', staff.email)
        staff.salary = data.get('salary', staff.salary)
        staff.commission_rate = data.get('commissionRate', staff.commission_rate)
        staff.status = data.get('status', staff.status)
        staff.updated_at = datetime.utcnow()
        staff.save()
        
        response = jsonify({'message': 'Staff updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@staff_bp.route('/<staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    """Delete staff member (soft delete by setting status to inactive)"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        staff = Staff.objects.get(id=staff_id)
        staff.status = 'inactive'
        staff.updated_at = datetime.utcnow()
        staff.save()
        response = jsonify({'message': 'Staff deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Staff not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

