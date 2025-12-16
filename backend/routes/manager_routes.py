from flask import Blueprint, request, jsonify
from models import db, Manager
from datetime import datetime

manager_bp = Blueprint('managers', __name__)

@manager_bp.route('/', methods=['GET'])
def get_managers():
    """Get all managers"""
    try:
        status = request.args.get('status', 'all')
        
        query = Manager.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        managers = query.order_by(Manager.created_at.desc()).all()
        
        return jsonify({
            'managers': [{
                'id': m.id,
                'name': f"{m.first_name} {m.last_name}".strip(),
                'firstName': m.first_name,
                'lastName': m.last_name,
                'email': m.email,
                'mobile': m.mobile,
                'salon': m.salon or '',
                'status': m.status
            } for m in managers]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@manager_bp.route('/<int:manager_id>', methods=['GET'])
def get_manager(manager_id):
    """Get single manager"""
    try:
        manager = Manager.query.get_or_404(manager_id)
        return jsonify({
            'id': manager.id,
            'firstName': manager.first_name,
            'lastName': manager.last_name,
            'email': manager.email,
            'mobile': manager.mobile,
            'salon': manager.salon or '',
            'status': manager.status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@manager_bp.route('/', methods=['POST'])
def create_manager():
    """Create new manager"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('firstName'):
            return jsonify({'error': 'First name is required'}), 400
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('mobile'):
            return jsonify({'error': 'Mobile is required'}), 400
        
        # Check if email already exists
        if Manager.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Manager with this email already exists'}), 400
        
        # Check if mobile already exists
        if Manager.query.filter_by(mobile=data.get('mobile')).first():
            return jsonify({'error': 'Manager with this mobile number already exists'}), 400
        
        manager = Manager(
            first_name=data.get('firstName'),
            last_name=data.get('lastName', ''),
            email=data.get('email'),
            mobile=data.get('mobile'),
            salon=data.get('salon', ''),
            password=data.get('password', ''),  # In production, hash this password
            status=data.get('status', 'active')
        )
        
        db.session.add(manager)
        db.session.commit()
        
        return jsonify({
            'id': manager.id,
            'message': 'Manager created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@manager_bp.route('/<int:manager_id>', methods=['PUT'])
def update_manager(manager_id):
    """Update manager"""
    try:
        manager = Manager.query.get_or_404(manager_id)
        data = request.json
        
        if 'firstName' in data:
            manager.first_name = data['firstName']
        if 'lastName' in data:
            manager.last_name = data.get('lastName', '')
        if 'email' in data:
            # Check if email is being changed and if it already exists
            if data['email'] != manager.email:
                if Manager.query.filter_by(email=data['email']).first():
                    return jsonify({'error': 'Manager with this email already exists'}), 400
            manager.email = data['email']
        if 'mobile' in data:
            # Check if mobile is being changed and if it already exists
            if data['mobile'] != manager.mobile:
                if Manager.query.filter_by(mobile=data['mobile']).first():
                    return jsonify({'error': 'Manager with this mobile number already exists'}), 400
            manager.mobile = data['mobile']
        if 'salon' in data:
            manager.salon = data['salon']
        if 'status' in data:
            manager.status = data['status']
        if 'password' in data and data['password']:
            manager.password = data['password']  # In production, hash this password
        
        manager.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Manager updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@manager_bp.route('/<int:manager_id>', methods=['DELETE'])
def delete_manager(manager_id):
    """Delete manager (soft delete by setting status to inactive)"""
    try:
        manager = Manager.query.get_or_404(manager_id)
        manager.status = 'inactive'
        manager.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Manager deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

