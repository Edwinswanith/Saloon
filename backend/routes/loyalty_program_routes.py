from flask import Blueprint, request, jsonify
from models import db, LoyaltyProgramSettings
from datetime import datetime

loyalty_program_bp = Blueprint('loyalty_program', __name__)

@loyalty_program_bp.route('/settings', methods=['GET'])
def get_loyalty_program_settings():
    """Get loyalty program settings"""
    try:
        settings = LoyaltyProgramSettings.get_settings()
        return jsonify({
            'enabled': settings.enabled,
            'earningRate': settings.earning_rate,
            'redemptionRate': settings.redemption_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loyalty_program_bp.route('/settings', methods=['PUT'])
def update_loyalty_program_settings():
    """Update loyalty program settings"""
    try:
        settings = LoyaltyProgramSettings.get_settings()
        data = request.json
        
        if 'enabled' in data:
            settings.enabled = bool(data['enabled'])
        if 'earningRate' in data:
            earning_rate = float(data['earningRate'])
            if earning_rate <= 0:
                return jsonify({'error': 'Earning rate must be greater than 0'}), 400
            settings.earning_rate = earning_rate
        if 'redemptionRate' in data:
            redemption_rate = float(data['redemptionRate'])
            if redemption_rate <= 0:
                return jsonify({'error': 'Redemption rate must be greater than 0'}), 400
            settings.redemption_rate = redemption_rate
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Loyalty program settings updated successfully',
            'enabled': settings.enabled,
            'earningRate': settings.earning_rate,
            'redemptionRate': settings.redemption_rate
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid value provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

