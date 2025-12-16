from flask import Blueprint, request, jsonify
from models import db, ReferralProgramSettings
from datetime import datetime

referral_program_bp = Blueprint('referral_program', __name__)

@referral_program_bp.route('/settings', methods=['GET'])
def get_referral_program_settings():
    """Get referral program settings"""
    try:
        settings = ReferralProgramSettings.get_settings()
        return jsonify({
            'enabled': settings.enabled,
            'rewardType': settings.reward_type,
            'referrerRewardPercentage': settings.referrer_reward_percentage,
            'refereeRewardPercentage': settings.referee_reward_percentage
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@referral_program_bp.route('/settings', methods=['PUT'])
def update_referral_program_settings():
    """Update referral program settings"""
    try:
        settings = ReferralProgramSettings.get_settings()
        data = request.json
        
        if 'enabled' in data:
            settings.enabled = bool(data['enabled'])
        if 'rewardType' in data:
            reward_type = data['rewardType'].lower()
            if reward_type not in ['percentage', 'fixed']:
                return jsonify({'error': 'Reward type must be "percentage" or "fixed"'}), 400
            settings.reward_type = reward_type
        if 'referrerRewardPercentage' in data:
            referrer_reward = float(data['referrerRewardPercentage'])
            if referrer_reward < 0 or referrer_reward > 100:
                return jsonify({'error': 'Referrer reward percentage must be between 0 and 100'}), 400
            settings.referrer_reward_percentage = referrer_reward
        if 'refereeRewardPercentage' in data:
            referee_reward = float(data['refereeRewardPercentage'])
            if referee_reward < 0 or referee_reward > 100:
                return jsonify({'error': 'Referee reward percentage must be between 0 and 100'}), 400
            settings.referee_reward_percentage = referee_reward
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Referral program settings updated successfully',
            'enabled': settings.enabled,
            'rewardType': settings.reward_type,
            'referrerRewardPercentage': settings.referrer_reward_percentage,
            'refereeRewardPercentage': settings.referee_reward_percentage
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid value provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

