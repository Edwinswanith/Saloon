from flask import Blueprint, request, jsonify
from models import Notification, to_dict
from utils.auth import require_auth
from utils.branch_filter import get_selected_branch

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/', methods=['GET'])
@require_auth
def list_notifications(current_user=None):
    """List notifications for the current user's role and branch"""
    try:
        user_role = current_user.get('role', '')
        user_id = str(current_user.get('user_id') or current_user.get('id', ''))

        branch = get_selected_branch(request, current_user)
        query = Notification.objects(for_roles=user_role, is_resolved=False)
        if branch:
            query = query.filter(branch=branch)

        notifications = query.order_by('-created_at').limit(50)

        result = []
        for n in notifications:
            data = to_dict(n)
            data['is_read'] = user_id in (n.read_by or [])
            result.append(data)

        unread_count = sum(1 for n in result if not n['is_read'])

        return jsonify({'notifications': result, 'unread_count': unread_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/<notification_id>/read', methods=['PUT'])
@require_auth
def mark_read(notification_id, current_user=None):
    """Mark a single notification as read for the current user"""
    try:
        user_id = str(current_user.get('user_id') or current_user.get('id', ''))
        n = Notification.objects(id=notification_id).first()
        if not n:
            return jsonify({'error': 'Notification not found'}), 404

        if user_id not in (n.read_by or []):
            n.read_by = (n.read_by or []) + [user_id]
            n.save()

        return jsonify({'message': 'Marked as read'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/read-all', methods=['PUT'])
@require_auth
def mark_all_read(current_user=None):
    """Mark all notifications as read for the current user"""
    try:
        user_role = current_user.get('role', '')
        user_id = str(current_user.get('user_id') or current_user.get('id', ''))

        branch = get_selected_branch(request, current_user)
        query = Notification.objects(for_roles=user_role, is_resolved=False)
        if branch:
            query = query.filter(branch=branch)

        for n in query:
            if user_id not in (n.read_by or []):
                n.read_by = (n.read_by or []) + [user_id]
                n.save()

        return jsonify({'message': 'All marked as read'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
