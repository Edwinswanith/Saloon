from flask import Blueprint, request, jsonify
from models import ReferralProgramSettings, Customer, Referral
from datetime import datetime
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

referral_program_bp = Blueprint('referral_program', __name__)

@referral_program_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@referral_program_bp.route('/settings', methods=['GET'])
@require_auth
def get_referral_program_settings(current_user=None):
    """Get referral program settings"""
    try:
        settings = ReferralProgramSettings.get_settings()
        response = jsonify({
            'enabled': settings.enabled,
            'rewardType': settings.reward_type,
            'referrerRewardPercentage': settings.referrer_reward_percentage,
            'refereeRewardPercentage': settings.referee_reward_percentage
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@referral_program_bp.route('/settings', methods=['PUT'])
@require_role('owner')
def update_referral_program_settings(current_user=None):
    """Update referral program settings (owner only)"""
    try:
        settings = ReferralProgramSettings.get_settings()
        data = request.json

        if 'enabled' in data:
            settings.enabled = bool(data['enabled'])
        if 'rewardType' in data:
            reward_type = data['rewardType'].lower()
            if reward_type not in ['percentage', 'fixed']:
                response = jsonify({'error': 'Reward type must be "percentage" or "fixed"'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            settings.reward_type = reward_type
        if 'referrerRewardPercentage' in data:
            referrer_reward = float(data['referrerRewardPercentage'])
            if referrer_reward < 0:
                response = jsonify({'error': 'Referrer reward must be a positive value'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            if settings.reward_type == 'percentage' and referrer_reward > 100:
                response = jsonify({'error': 'Referrer reward percentage must be between 0 and 100'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            settings.referrer_reward_percentage = referrer_reward
        if 'refereeRewardPercentage' in data:
            referee_reward = float(data['refereeRewardPercentage'])
            if referee_reward < 0:
                response = jsonify({'error': 'Referee reward must be a positive value'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            if settings.reward_type == 'percentage' and referee_reward > 100:
                response = jsonify({'error': 'Referee reward percentage must be between 0 and 100'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            settings.referee_reward_percentage = referee_reward

        settings.updated_at = datetime.utcnow()
        settings.save()

        response = jsonify({
            'message': 'Referral program settings updated successfully',
            'enabled': settings.enabled,
            'rewardType': settings.reward_type,
            'referrerRewardPercentage': settings.referrer_reward_percentage,
            'refereeRewardPercentage': settings.referee_reward_percentage
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except ValueError as e:
        response = jsonify({'error': 'Invalid value provided'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@referral_program_bp.route('/validate-code', methods=['GET'])
@require_auth
def validate_referral_code(current_user=None):
    """Validate a referral code and return the referrer info"""
    try:
        code = request.args.get('code', '').strip()
        if not code:
            response = jsonify({'valid': False, 'error': 'Referral code is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Check if referral program is enabled
        settings = ReferralProgramSettings.get_settings()
        if not settings.enabled:
            response = jsonify({'valid': False, 'error': 'Referral program is not active'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Find customer with this referral code
        referrer = Customer.objects(referral_code=code).first()
        if not referrer:
            response = jsonify({'valid': False, 'error': 'Invalid referral code'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        response = jsonify({
            'valid': True,
            'referrerId': str(referrer.id),
            'referrerName': f"{referrer.first_name or ''} {referrer.last_name or ''}".strip()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@referral_program_bp.route('/referrals', methods=['GET'])
@require_auth
def get_referrals(current_user=None):
    """Get list of referrals with optional branch filter"""
    try:
        branch = get_selected_branch(request, current_user)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Referral.objects()
        if branch:
            query = query.filter(branch=branch)

        total = query.count()
        referrals = list(query.order_by('-created_at').skip((page - 1) * per_page).limit(per_page))

        result = []
        for ref in referrals:
            referrer_name = ''
            referee_name = ''
            try:
                if ref.referrer:
                    ref.referrer.reload()
                    referrer_name = f"{ref.referrer.first_name or ''} {ref.referrer.last_name or ''}".strip()
            except Exception:
                pass
            try:
                if ref.referee:
                    ref.referee.reload()
                    referee_name = f"{ref.referee.first_name or ''} {ref.referee.last_name or ''}".strip()
            except Exception:
                pass

            result.append({
                'id': str(ref.id),
                'referrerName': referrer_name,
                'refereeName': referee_name,
                'refereeDiscount': ref.referee_discount,
                'referrerReward': ref.referrer_reward,
                'referrerRewardRedeemed': ref.referrer_reward_redeemed,
                'createdAt': ref.created_at.isoformat() if ref.created_at else None
            })

        response = jsonify({
            'referrals': result,
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
