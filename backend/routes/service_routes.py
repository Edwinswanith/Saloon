from flask import Blueprint, request, jsonify
from models import Service, ServiceGroup, to_dict
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId

service_bp = Blueprint('services', __name__)

@service_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Service Group Routes
@service_bp.route('/groups', methods=['GET'])
def get_service_groups():
    """Get all service groups"""
    groups = ServiceGroup.objects.order_by('display_order')
    
    response = jsonify({
        'groups': [{
            'id': str(g.id),
            'name': g.name,
            'count': Service.objects(group=g).count(),
            'displayOrder': g.display_order
        } for g in groups]
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@service_bp.route('/groups', methods=['POST'])
def create_service_group():
    """Create new service group"""
    data = request.json
    
    group = ServiceGroup(
        name=data.get('name', ''),
        display_order=data.get('displayOrder', 0)
    )
    group.save()
    
    response = jsonify({'id': str(group.id), 'message': 'Service group created successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 201

@service_bp.route('/groups/<group_id>', methods=['PUT'])
def update_service_group(group_id):
    """Update service group"""
    try:
        if not ObjectId.is_valid(group_id):
            return jsonify({'error': 'Invalid group ID format'}), 400
        group = ServiceGroup.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({'error': 'Service group not found'}), 404
    
    data = request.json
    
    group.name = data.get('name', group.name)
    group.display_order = data.get('displayOrder', group.display_order)
    group.save()
    
    response = jsonify({'message': 'Service group updated successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@service_bp.route('/groups/<group_id>', methods=['DELETE'])
def delete_service_group(group_id):
    """Delete service group"""
    try:
        if not ObjectId.is_valid(group_id):
            return jsonify({'error': 'Invalid group ID format'}), 400
        group = ServiceGroup.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({'error': 'Service group not found'}), 404
    
    group.delete()
    response = jsonify({'message': 'Service group deleted successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# Service Routes
@service_bp.route('/', methods=['GET'])
def get_services():
    """Get all services, optionally filtered by group"""
    group_id = request.args.get('group_id', type=str)
    search = request.args.get('search', '')
    
    query = Service.objects(status='active')
    
    if group_id:
        if ObjectId.is_valid(group_id):
            try:
                group = ServiceGroup.objects.get(id=group_id)
                query = query.filter(group=group)
            except (DoesNotExist, ValidationError):
                pass
    
    if search:
        query = query.filter(name__icontains=search)
    
    services = query
    
    response = jsonify({
        'services': [{
            'id': str(s.id),
            'name': s.name,
            'groupId': str(s.group.id) if s.group else None,
            'groupName': s.group.name if s.group else None,
            'price': s.price,
            'duration': s.duration,
            'description': s.description
        } for s in services]
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@service_bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    """Get single service"""
    try:
        if not ObjectId.is_valid(service_id):
            return jsonify({'error': 'Invalid service ID format'}), 400
        service = Service.objects.get(id=service_id)
    except DoesNotExist:
        return jsonify({'error': 'Service not found'}), 404
    except ValidationError:
        return jsonify({'error': 'Invalid service ID format'}), 400
    
    response = jsonify({
        'id': str(service.id),
        'name': service.name,
        'groupId': str(service.group.id) if service.group else None,
        'price': service.price,
        'duration': service.duration,
        'description': service.description
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@service_bp.route('/', methods=['POST'])
def create_service():
    """Create new service"""
    data = request.json
    
    # Get group reference
    group = None
    if data.get('groupId'):
        if not ObjectId.is_valid(data.get('groupId')):
            return jsonify({'error': 'Invalid group ID format'}), 400
        try:
            group = ServiceGroup.objects.get(id=data.get('groupId'))
        except DoesNotExist:
            return jsonify({'error': 'Service group not found'}), 400
        except ValidationError:
            return jsonify({'error': 'Invalid group ID format'}), 400
    
    service = Service(
        name=data.get('name', ''),
        group=group,
        price=data.get('price', 0.0),
        duration=data.get('duration'),
        description=data.get('description', ''),
        status=data.get('status', 'active')
    )
    service.save()
    
    response = jsonify({'id': str(service.id), 'message': 'Service created successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 201

@service_bp.route('/<service_id>', methods=['PUT'])
def update_service(service_id):
    """Update service"""
    try:
        if not ObjectId.is_valid(service_id):
            return jsonify({'error': 'Invalid service ID format'}), 400
        service = Service.objects.get(id=service_id)
    except DoesNotExist:
        return jsonify({'error': 'Service not found'}), 404
    
    data = request.json
    
    service.name = data.get('name', service.name)
    if 'groupId' in data:
        if data['groupId']:
            if not ObjectId.is_valid(data['groupId']):
                return jsonify({'error': 'Invalid group ID format'}), 400
            try:
                service.group = ServiceGroup.objects.get(id=data['groupId'])
            except DoesNotExist:
                return jsonify({'error': 'Service group not found'}), 400
            except ValidationError:
                return jsonify({'error': 'Invalid group ID format'}), 400
        else:
            service.group = None
    service.price = data.get('price', service.price)
    service.duration = data.get('duration', service.duration)
    service.description = data.get('description', service.description)
    service.status = data.get('status', service.status)
    service.updated_at = datetime.utcnow()
    service.save()
    
    response = jsonify({'message': 'Service updated successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@service_bp.route('/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    """Delete service (soft delete)"""
    try:
        if not ObjectId.is_valid(service_id):
            return jsonify({'error': 'Invalid service ID format'}), 400
        service = Service.objects.get(id=service_id)
    except DoesNotExist:
        return jsonify({'error': 'Service not found'}), 404
    
    service.status = 'inactive'
    service.updated_at = datetime.utcnow()
    service.save()
    response = jsonify({'message': 'Service deleted successfully'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

