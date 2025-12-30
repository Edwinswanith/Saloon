"""
Branch management routes
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Branch
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch, get_user_branch
from mongoengine.errors import ValidationError, DoesNotExist
from bson import ObjectId

branch_bp = Blueprint('branch', __name__)


@branch_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


@branch_bp.route('/branches', methods=['GET'])
def list_branches():
    """Get all branches"""
    try:
        branches = Branch.objects(is_active=True).order_by('name')
        
        result = []
        for branch in branches:
            result.append({
                'id': str(branch.id),
                'name': branch.name,
                'address': branch.address,
                'city': branch.city,
                'phone': branch.phone,
                'email': branch.email,
                'is_active': branch.is_active,
                'created_at': branch.created_at.isoformat() if branch.created_at else None
            })
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@branch_bp.route('/branches/<branch_id>', methods=['GET'])
@require_auth
def get_branch(branch_id, current_user=None):
    """Get single branch by ID"""
    try:
        if not ObjectId.is_valid(branch_id):
            response = jsonify({'error': 'Invalid branch ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = Branch.objects(id=branch_id).first()
        if not branch:
            response = jsonify({'error': 'Branch not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        result = {
            'id': str(branch.id),
            'name': branch.name,
            'address': branch.address,
            'city': branch.city,
            'phone': branch.phone,
            'email': branch.email,
            'is_active': branch.is_active,
            'created_at': branch.created_at.isoformat() if branch.created_at else None,
            'updated_at': branch.updated_at.isoformat() if branch.updated_at else None
        }
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@branch_bp.route('/branches', methods=['POST'])
@require_role('owner')
def create_branch(current_user=None):
    """Create new branch (Owner only)"""
    try:
        
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate required fields
        if not data.get('name'):
            response = jsonify({'error': 'Branch name is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = Branch(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city', 'Chennai'),
            phone=data.get('phone'),
            email=data.get('email'),
            is_active=data.get('is_active', True)
        )
        branch.save()
        
        result = {
            'id': str(branch.id),
            'name': branch.name,
            'address': branch.address,
            'city': branch.city,
            'phone': branch.phone,
            'email': branch.email,
            'is_active': branch.is_active,
            'created_at': branch.created_at.isoformat() if branch.created_at else None
        }
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@branch_bp.route('/branches/<branch_id>', methods=['PUT'])
@require_role('owner')
def update_branch(branch_id, current_user=None):
    """Update branch (Owner only)"""
    try:
        
        if not ObjectId.is_valid(branch_id):
            response = jsonify({'error': 'Invalid branch ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = Branch.objects(id=branch_id).first()
        if not branch:
            response = jsonify({'error': 'Branch not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Update fields
        if 'name' in data:
            branch.name = data['name']
        if 'address' in data:
            branch.address = data['address']
        if 'city' in data:
            branch.city = data['city']
        if 'phone' in data:
            branch.phone = data['phone']
        if 'email' in data:
            branch.email = data['email']
        if 'is_active' in data:
            branch.is_active = data['is_active']
        
        branch.updated_at = datetime.utcnow()
        branch.save()
        
        result = {
            'id': str(branch.id),
            'name': branch.name,
            'address': branch.address,
            'city': branch.city,
            'phone': branch.phone,
            'email': branch.email,
            'is_active': branch.is_active,
            'updated_at': branch.updated_at.isoformat() if branch.updated_at else None
        }
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@branch_bp.route('/branches/current', methods=['GET'])
@require_auth
def get_current_branch(current_user=None):
    """Get current user's branch"""
    try:
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'branch': None})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        result = {
            'id': str(branch.id),
            'name': branch.name,
            'address': branch.address,
            'city': branch.city,
            'phone': branch.phone,
            'email': branch.email,
            'is_active': branch.is_active
        }
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@branch_bp.route('/branches', methods=['OPTIONS'])
def handle_preflight():
    """Handle CORS preflight requests"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Branch-Id')
    return response

