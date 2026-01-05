from flask import Blueprint, request, jsonify
from models import LoyaltyProgramSettings, Customer, LoyaltyPointsTransaction
from datetime import datetime
from utils.auth import require_role, require_auth, get_current_user
from bson import ObjectId

loyalty_program_bp = Blueprint('loyalty_program', __name__)

@loyalty_program_bp.route('/settings', methods=['GET'])
def get_loyalty_program_settings():
    """Get loyalty program settings"""
    try:
        settings = LoyaltyProgramSettings.get_settings()
        return jsonify({
            'enabled': settings.enabled,
            'earningRate': settings.earning_rate,
            'redemptionRate': settings.redemption_rate,
            'minimumPointsToRedeem': settings.minimum_points_to_redeem
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loyalty_program_bp.route('/settings', methods=['PUT'])
@require_role('owner')
def update_loyalty_program_settings(current_user=None):
    """Update loyalty program settings (Owner only)"""
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
        if 'minimumPointsToRedeem' in data:
            minimum_points = int(data['minimumPointsToRedeem'])
            if minimum_points < 0:
                return jsonify({'error': 'Minimum points must be 0 or greater'}), 400
            settings.minimum_points_to_redeem = minimum_points
        
        settings.updated_at = datetime.utcnow()
        settings.save()
        
        return jsonify({
            'message': 'Loyalty program settings updated successfully',
            'enabled': settings.enabled,
            'earningRate': settings.earning_rate,
            'redemptionRate': settings.redemption_rate,
            'minimumPointsToRedeem': settings.minimum_points_to_redeem
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid value provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loyalty_program_bp.route('/redeem', methods=['POST'])
@require_auth
def calculate_points_redemption(current_user=None):
    """Calculate discount amount for points redemption (preview only, doesn't apply)"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        points_to_use = int(data.get('points_to_use', 0))
        
        if not customer_id:
            return jsonify({'error': 'Customer ID is required'}), 400
        
        if points_to_use <= 0:
            return jsonify({'error': 'Points to use must be greater than 0'}), 400
        
        # Get customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get loyalty settings
        loyalty_settings = LoyaltyProgramSettings.get_settings()
        if not loyalty_settings.enabled:
            return jsonify({'error': 'Loyalty program is not enabled'}), 400
        
        # Validate minimum points requirement
        if points_to_use < loyalty_settings.minimum_points_to_redeem:
            return jsonify({
                'error': f'Minimum {loyalty_settings.minimum_points_to_redeem} points required to redeem'
            }), 400
        
        # Validate customer has enough points
        if customer.loyalty_points < points_to_use:
            return jsonify({
                'error': f'Insufficient points. Available: {customer.loyalty_points}, Requested: {points_to_use}'
            }), 400
        
        # Calculate discount amount
        redemption_rate = float(loyalty_settings.redemption_rate) if loyalty_settings.redemption_rate else 1.0
        discount_amount = float(points_to_use) / float(redemption_rate)
        
        return jsonify({
            'discount_amount': discount_amount,
            'points_to_use': points_to_use,
            'available_points': customer.loyalty_points
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid value provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loyalty_program_bp.route('/transactions/<customer_id>', methods=['GET'])
@require_auth
def get_points_transactions(current_user=None, customer_id=None):
    """Get loyalty points transaction history for a customer"""
    try:
        # Validate customer exists
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get transactions
        transactions = LoyaltyPointsTransaction.objects(customer=customer).order_by('-created_at')
        
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'id': str(transaction.id),
                'transaction_type': transaction.transaction_type,
                'points': transaction.points,
                'balance_after': transaction.balance_after,
                'description': transaction.description,
                'bill_id': str(transaction.bill.id) if transaction.bill else None,
                'created_at': transaction.created_at.isoformat()
            })
        
        return jsonify({
            'transactions': transactions_data,
            'current_balance': customer.loyalty_points
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

