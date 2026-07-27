from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Offer, Branch
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

offer_bp = Blueprint('offers', __name__)


@offer_bp.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


def _serialize_offer(offer):
    return {
        'id': str(offer.id),
        'name': offer.name,
        'description': offer.description or '',
        'offer_type': offer.offer_type,
        'discount_percentage': float(offer.discount_percentage or 0),
        'start_date': offer.start_date.isoformat() if offer.start_date else None,
        'end_date': offer.end_date.isoformat() if offer.end_date else None,
        'status': offer.status,
        'branch_id': str(offer.branch.id) if offer.branch else None,
        'branch_name': offer.branch.name if offer.branch else None,
        'created_by_name': offer.created_by_name or '',
        'created_at': offer.created_at.isoformat() if offer.created_at else None,
        'updated_at': offer.updated_at.isoformat() if offer.updated_at else None,
        'is_currently_valid': offer.is_currently_valid(),
    }


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Accept full ISO datetime
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        pass
    try:
        # Plain YYYY-MM-DD → midnight UTC
        return datetime.strptime(str(value), '%Y-%m-%d')
    except Exception:
        return None


def _validate_offer_payload(data, partial=False):
    errors = []
    name = (data.get('name') or '').strip()
    if not partial and not name:
        errors.append('Offer name is required')

    if 'offer_type' in data:
        if data['offer_type'] not in ('general', 'membership'):
            errors.append("offer_type must be 'general' or 'membership'")

    if 'discount_percentage' in data:
        try:
            pct = float(data['discount_percentage'])
            if pct < 0 or pct > 100:
                errors.append('discount_percentage must be between 0 and 100')
        except (TypeError, ValueError):
            errors.append('discount_percentage must be a number')

    start = _parse_date(data.get('start_date')) if 'start_date' in data else None
    end = _parse_date(data.get('end_date')) if 'end_date' in data else None
    if 'start_date' in data and not start:
        errors.append('Invalid start_date')
    if 'end_date' in data and not end:
        errors.append('Invalid end_date')
    if start and end and end < start:
        errors.append('end_date must be on or after start_date')

    if 'status' in data and data['status'] not in ('active', 'inactive'):
        errors.append("status must be 'active' or 'inactive'")

    return errors, start, end


@offer_bp.route('/', methods=['GET'])
@require_auth
def list_offers(current_user=None):
    """List all offers for the current branch (and unscoped offers).

    Query params:
        status: 'active' | 'inactive' (optional)
        type: 'general' | 'membership' (optional)
        only_valid: '1' to return only currently-valid offers
    """
    try:
        branch = get_selected_branch(request, current_user)
        query = Offer.objects()

        if branch:
            # Branch-scoped + globally available offers (branch=None)
            from mongoengine import Q
            query = query.filter(Q(branch=branch) | Q(branch=None))

        status = request.args.get('status')
        if status:
            query = query.filter(status=status)

        offer_type = request.args.get('type')
        if offer_type:
            query = query.filter(offer_type=offer_type)

        offers = list(query.order_by('-created_at'))
        only_valid = request.args.get('only_valid') in ('1', 'true', 'yes')
        if only_valid:
            offers = [o for o in offers if o.is_currently_valid()]

        result = [_serialize_offer(o) for o in offers]
        response = jsonify({'offers': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error listing offers: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@offer_bp.route('/active', methods=['GET'])
@require_auth
def active_offers(current_user=None):
    """Convenience: only currently-valid offers for the selected branch."""
    try:
        branch = get_selected_branch(request, current_user)
        from mongoengine import Q
        query = Offer.objects(status='active')
        if branch:
            query = query.filter(Q(branch=branch) | Q(branch=None))
        offers = [o for o in query if o.is_currently_valid()]
        result = [_serialize_offer(o) for o in offers]
        response = jsonify({'offers': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error fetching active offers: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@offer_bp.route('/', methods=['POST'])
@require_role('staff', 'manager', 'owner')
def create_offer(current_user=None):
    try:
        data = request.json or {}
        errors, start, end = _validate_offer_payload(data, partial=False)
        if not start:
            errors.append('start_date is required')
        if not end:
            errors.append('end_date is required')
        if 'discount_percentage' not in data:
            errors.append('discount_percentage is required')
        if errors:
            response = jsonify({'error': '; '.join(errors)})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        branch = get_selected_branch(request, current_user)
        offer = Offer(
            name=data['name'].strip(),
            description=(data.get('description') or '').strip() or None,
            offer_type=data.get('offer_type', 'general'),
            discount_percentage=float(data['discount_percentage']),
            start_date=start,
            end_date=end,
            status=data.get('status', 'active'),
            branch=branch if branch else None,
            created_by_name=current_user.get('name', 'Unknown') if current_user else 'Unknown',
        )
        offer.save()
        response = jsonify({'offer': _serialize_offer(offer)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        print(f"Error creating offer: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@offer_bp.route('/<offer_id>', methods=['PUT'])
@require_role('staff', 'manager', 'owner')
def update_offer(offer_id, current_user=None):
    try:
        offer = Offer.objects(id=offer_id).first()
        if not offer:
            response = jsonify({'error': 'Offer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        data = request.json or {}
        errors, start, end = _validate_offer_payload(data, partial=True)
        if errors:
            response = jsonify({'error': '; '.join(errors)})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if 'name' in data:
            offer.name = data['name'].strip()
        if 'description' in data:
            offer.description = (data.get('description') or '').strip() or None
        if 'offer_type' in data:
            offer.offer_type = data['offer_type']
        if 'discount_percentage' in data:
            offer.discount_percentage = float(data['discount_percentage'])
        if start:
            offer.start_date = start
        if end:
            offer.end_date = end
        if 'status' in data:
            offer.status = data['status']

        offer.updated_at = datetime.utcnow()
        offer.save()
        response = jsonify({'offer': _serialize_offer(offer)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error updating offer: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@offer_bp.route('/<offer_id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_offer(offer_id, current_user=None):
    """Soft-delete by marking the offer inactive."""
    try:
        offer = Offer.objects(id=offer_id).first()
        if not offer:
            response = jsonify({'error': 'Offer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        offer.status = 'inactive'
        offer.updated_at = datetime.utcnow()
        offer.save()
        response = jsonify({'message': 'Offer deactivated', 'offer': _serialize_offer(offer)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error deleting offer: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
