from flask import Blueprint, request, jsonify
from mongoengine import Q
from datetime import datetime
from models import ServiceRecoveryCase, Feedback, Customer, Bill, Manager
from utils.auth import require_auth, require_role, get_current_user
from utils.branch_filter import get_selected_branch, filter_by_branch
from models import to_dict

service_recovery_bp = Blueprint('service_recovery', __name__)

@service_recovery_bp.route('/', methods=['GET'])
@require_auth
def list_cases(current_user=None):
    """List service recovery cases with filters"""
    try:
        status = request.args.get('status')
        issue_type = request.args.get('issue_type')
        assigned_manager_id = request.args.get('assigned_manager_id')
        
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        query = Q()
        
        # Filter by branch if specified
        if branch:
            query &= Q(branch=branch)
        
        if status:
            query &= Q(status=status)
        if issue_type:
            query &= Q(issue_type=issue_type)
        if assigned_manager_id:
            query &= Q(assigned_manager=assigned_manager_id)
        
        # Force evaluation by converting to list
        cases = list(ServiceRecoveryCase.objects(query).order_by('-created_at'))
        
        result = []
        for case in cases:
            data = to_dict(case)
            if case.customer:
                data['customer_name'] = f"{case.customer.first_name} {case.customer.last_name or ''}".strip()
            if case.assigned_manager:
                data['assigned_manager_name'] = f"{case.assigned_manager.first_name} {case.assigned_manager.last_name or ''}".strip()
            result.append(data)
        
        response = jsonify({'cases': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@service_recovery_bp.route('/<case_id>', methods=['GET'])
@require_auth
def get_case(case_id, current_user=None):
    """Get a single service recovery case"""
    try:
        case = ServiceRecoveryCase.objects(id=case_id).first()
        if not case:
            response = jsonify({'error': 'Service recovery case not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        result = to_dict(case)
        if case.customer:
            result['customer_name'] = f"{case.customer.first_name} {case.customer.last_name or ''}".strip()
        if case.assigned_manager:
            result['assigned_manager_name'] = f"{case.assigned_manager.first_name} {case.assigned_manager.last_name or ''}".strip()
        
        response = jsonify({'case': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@service_recovery_bp.route('/<case_id>/assign', methods=['PUT'])
@require_role('manager', 'owner')
def assign_manager(case_id, current_user=None):
    """Assign a manager to a service recovery case"""
    try:
        case = ServiceRecoveryCase.objects(id=case_id).first()
        if not case:
            response = jsonify({'error': 'Service recovery case not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        manager_id = data.get('manager_id')
        
        if manager_id:
            manager = Manager.objects(id=manager_id).first()
            if manager:
                case.assigned_manager = manager
                case.status = 'in_progress'
                case.updated_at = datetime.utcnow()
                case.save()
                
                result = to_dict(case)
                response = jsonify({'case': result, 'message': 'Manager assigned successfully'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 200
        
        response = jsonify({'error': 'Manager ID required'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@service_recovery_bp.route('/<case_id>/resolve', methods=['PUT'])
@require_role('manager', 'owner')
def resolve_case(case_id, current_user=None):
    """Mark a service recovery case as resolved"""
    try:
        case = ServiceRecoveryCase.objects(id=case_id).first()
        if not case:
            response = jsonify({'error': 'Service recovery case not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        resolution_notes = data.get('resolution_notes', '')
        
        case.resolution_notes = resolution_notes
        case.status = 'resolved'
        case.resolved_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        case.save()
        
        result = to_dict(case)
        response = jsonify({'case': result, 'message': 'Case resolved successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@service_recovery_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats(current_user=None):
    """Get statistics for service recovery cases"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Build base query with branch filter
        base_query = Q()
        if branch:
            base_query &= Q(branch=branch)
        
        total = ServiceRecoveryCase.objects(base_query).count()
        open_query = base_query & Q(status='open')
        in_progress_query = base_query & Q(status='in_progress')
        resolved_query = base_query & Q(status='resolved')
        closed_query = base_query & Q(status='closed')
        
        open_count = ServiceRecoveryCase.objects(open_query).count()
        in_progress_count = ServiceRecoveryCase.objects(in_progress_query).count()
        resolved_count = ServiceRecoveryCase.objects(resolved_query).count()
        closed_count = ServiceRecoveryCase.objects(closed_query).count()
        
        resolution_rate = (resolved_count / total * 100) if total > 0 else 0
        
        stats = {
            'total': total,
            'open': open_count,
            'in_progress': in_progress_count,
            'resolved': resolved_count,
            'closed': closed_count,
            'resolution_rate': round(resolution_rate, 2)
        }
        
        response = jsonify({'stats': stats})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

