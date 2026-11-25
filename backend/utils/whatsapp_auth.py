"""Authorization boundary for the production WhatsApp integration."""
from functools import wraps

from bson import ObjectId
from flask import jsonify

from models import Owner
from utils.auth import get_current_user
from utils.branch_filter import is_demo_user


def require_whatsapp_owner(view):
    """Allow only an active, non-demo Owner account."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401

        user_id = user.get('user_id')
        if (
            user.get('role') != 'owner'
            or not user_id
            or not ObjectId.is_valid(user_id)
        ):
            return jsonify({'error': 'Owner access required'}), 403

        owner = Owner.objects(
            id=user_id,
            is_active=True,
            status='active',
        ).first()
        if not owner or is_demo_user(owner):
            return jsonify({'error': 'Owner access required'}), 403

        kwargs['current_user'] = user
        return view(*args, **kwargs)

    return wrapped
