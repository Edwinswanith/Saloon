"""Runtime-scoped authorization boundary for the WhatsApp integration."""
from functools import wraps

from bson import ObjectId
from flask import jsonify

from models import Owner
from utils.auth import get_current_user
from utils.branch_filter import is_demo_user
from utils.env_config import get_app_runtime


def require_whatsapp_owner(view):
    """Allow only an active Owner belonging to the configured runtime."""
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
        runtime = get_app_runtime()
        owner_is_demo = bool(owner and is_demo_user(owner))
        if (
            not owner
            or (runtime == 'production' and owner_is_demo)
            or (runtime == 'demo' and not owner_is_demo)
        ):
            return jsonify({'error': 'Owner access required'}), 403

        kwargs['current_user'] = user
        return view(*args, **kwargs)

    return wrapped
