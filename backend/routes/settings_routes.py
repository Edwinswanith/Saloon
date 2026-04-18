from flask import Blueprint, request, jsonify
from datetime import datetime
from models import BusinessSettings
from utils.auth import require_role
from utils.redis_cache import clear_cache

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/business', methods=['GET'])
def get_business_settings():
    """Public endpoint returning the business display name and logo."""
    try:
        settings = BusinessSettings.get_instance()
        response = jsonify({
            'name': settings.name or 'Priyanka Nature Cure',
            'logo_url': settings.logo_url or ''
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@settings_bp.route('/business', methods=['PUT'])
@require_role('owner')
def update_business_settings(current_user=None):
    """Update the business display name / logo (Owner only)."""
    try:
        data = request.get_json() or {}
        settings = BusinessSettings.get_instance()

        if 'name' in data:
            name = (data.get('name') or '').strip()
            if not name:
                return jsonify({'error': 'Name cannot be empty'}), 400
            settings.name = name[:120]

        if 'logo_url' in data:
            settings.logo_url = (data.get('logo_url') or '').strip()[:500]

        settings.updated_at = datetime.utcnow()
        settings.save()

        # Invalidate the cached GET response so clients pick up the new name immediately.
        clear_cache(pattern='/api/settings/business')

        response = jsonify({
            'name': settings.name,
            'logo_url': settings.logo_url or ''
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
