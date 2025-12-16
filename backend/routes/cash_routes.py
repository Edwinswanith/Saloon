from flask import Blueprint, request, jsonify
from models import CashTransaction
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId

cash_bp = Blueprint('cash', __name__)

@cash_bp.route('/transactions', methods=['GET'])
def get_cash_transactions():
    """Get cash transactions with optional filters"""
    try:
        # Query parameters
        transaction_type = request.args.get('transaction_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date = request.args.get('date')  # Single date filter (for daily view)
        view = request.args.get('view', 'daily')  # daily or monthly

        query = CashTransaction.objects

        # Apply filters
        if transaction_type:
            query = query.filter(transaction_type=transaction_type)
        
        # Handle single date filter (for daily view)
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(transaction_date=target_date)
        else:
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(transaction_date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(transaction_date__lte=end)

        transactions = query.order_by('-transaction_date', '-transaction_time')

        return jsonify({
            'transactions': [{
                'id': str(t.id),
                'transaction_type': t.transaction_type,
                'amount': t.amount,
                'reason': t.reason,
                'notes': t.notes,
                'transaction_date': t.transaction_date.isoformat() if t.transaction_date else None,
                'transaction_time': t.transaction_time if t.transaction_time else None,  # Already a string
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/transactions/<id>', methods=['GET'])
def get_cash_transaction(id):
    """Get a single cash transaction by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid transaction ID format'}), 400
        transaction = CashTransaction.objects.get(id=id)
        return jsonify({
            'id': str(transaction.id),
            'transaction_type': transaction.transaction_type,
            'amount': transaction.amount,
            'reason': transaction.reason,
            'notes': transaction.notes,
            'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            'transaction_time': transaction.transaction_time if transaction.transaction_time else None,  # Already a string
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/in', methods=['POST'])
def add_cash_in():
    """Add cash in transaction"""
    try:
        data = request.get_json()

        # Parse date and time (time should be string in HH:MM:SS format)
        transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date() if 'transaction_date' in data else date.today()
        transaction_time = data.get('transaction_time', datetime.now().strftime('%H:%M:%S'))
        # Ensure time is string, not time object
        if isinstance(transaction_time, str):
            # Clean up time string
            if '.' in transaction_time:
                transaction_time = transaction_time.split('.')[0]
        else:
            transaction_time = transaction_time.strftime('%H:%M:%S') if hasattr(transaction_time, 'strftime') else str(transaction_time)

        transaction = CashTransaction(
            transaction_type='in',
            amount=data['amount'],
            reason=data.get('reason'),
            notes=data.get('notes'),
            transaction_date=transaction_date,
            transaction_time=transaction_time  # Store as string
        )
        transaction.save()

        return jsonify({
            'id': str(transaction.id),
            'message': 'Cash in transaction added successfully',
            'data': {
                'id': str(transaction.id),
                'amount': transaction.amount
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/out', methods=['POST'])
def add_cash_out():
    """Add cash out transaction"""
    try:
        data = request.get_json()

        # Parse date and time (time should be string in HH:MM:SS format)
        transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date() if 'transaction_date' in data else date.today()
        transaction_time = data.get('transaction_time', datetime.now().strftime('%H:%M:%S'))
        # Ensure time is string, not time object
        if isinstance(transaction_time, str):
            # Clean up time string
            if '.' in transaction_time:
                transaction_time = transaction_time.split('.')[0]
        else:
            transaction_time = transaction_time.strftime('%H:%M:%S') if hasattr(transaction_time, 'strftime') else str(transaction_time)

        transaction = CashTransaction(
            transaction_type='out',
            amount=data['amount'],
            reason=data.get('reason'),
            notes=data.get('notes'),
            transaction_date=transaction_date,
            transaction_time=transaction_time  # Store as string
        )
        transaction.save()

        return jsonify({
            'id': str(transaction.id),
            'message': 'Cash out transaction added successfully',
            'data': {
                'id': str(transaction.id),
                'amount': transaction.amount
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/transactions/<id>', methods=['PUT'])
def update_cash_transaction(id):
    """Update a cash transaction"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid transaction ID format'}), 400
        transaction = CashTransaction.objects.get(id=id)
        data = request.get_json()

        transaction.transaction_type = data.get('transaction_type', transaction.transaction_type)
        transaction.amount = data.get('amount', transaction.amount)
        transaction.reason = data.get('reason', transaction.reason)
        transaction.notes = data.get('notes', transaction.notes)

        # Update date and time if provided
        if 'transaction_date' in data:
            transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        if 'transaction_time' in data:
            # Ensure time is string
            time_str = data['transaction_time']
            if isinstance(time_str, str):
                if '.' in time_str:
                    time_str = time_str.split('.')[0]
                transaction.transaction_time = time_str
            else:
                transaction.transaction_time = time_str.strftime('%H:%M:%S') if hasattr(time_str, 'strftime') else str(time_str)

        transaction.save()

        return jsonify({
            'id': str(transaction.id),
            'message': 'Cash transaction updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/transactions/<id>', methods=['DELETE'])
def delete_cash_transaction(id):
    """Delete a cash transaction"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid transaction ID format'}), 400
        transaction = CashTransaction.objects.get(id=id)
        transaction.delete()

        return jsonify({'message': 'Cash transaction deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/summary', methods=['GET'])
def get_cash_summary():
    """Get cash flow summary"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date = request.args.get('date')  # Single date filter (for daily view)

        query = CashTransaction.objects

        # Handle single date filter (for daily view)
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(transaction_date=target_date)
        else:
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(transaction_date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(transaction_date__lte=end)

        transactions = list(query)

        cash_in = sum([float(t.amount) for t in transactions if t.transaction_type == 'in'])
        cash_out = sum([float(t.amount) for t in transactions if t.transaction_type == 'out'])
        net_cash = cash_in - cash_out

        return jsonify({
            'total_in': cash_in,
            'total_out': cash_out,
            'net_flow': net_cash,
            'cash_in': cash_in,  # Keep for backward compatibility
            'cash_out': cash_out,
            'net_cash': net_cash,
            'total_transactions': len(transactions),
            'in_transactions': len([t for t in transactions if t.transaction_type == 'in']),
            'out_transactions': len([t for t in transactions if t.transaction_type == 'out'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/daily-summary', methods=['GET'])
def get_daily_cash_summary():
    """Get daily cash summary grouped by date"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = CashTransaction.objects

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(transaction_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(transaction_date__lte=end)

        transactions = list(query)

        # Group by date
        daily_summary = {}
        for t in transactions:
            date_key = t.transaction_date.isoformat() if t.transaction_date else None
            if not date_key:
                continue
            if date_key not in daily_summary:
                daily_summary[date_key] = {'in': 0.0, 'out': 0.0, 'net': 0.0}

            if t.transaction_type == 'in':
                daily_summary[date_key]['in'] += float(t.amount) if t.amount else 0.0
            else:
                daily_summary[date_key]['out'] += float(t.amount) if t.amount else 0.0

            daily_summary[date_key]['net'] = daily_summary[date_key]['in'] - daily_summary[date_key]['out']

        return jsonify({
            'daily_summary': [
                {
                    'date': date_key,
                    'cash_in': values['in'],
                    'cash_out': values['out'],
                    'net_cash': values['net']
                }
                for date_key, values in daily_summary.items()
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/balance', methods=['GET'])
def get_cash_balance():
    """Get current cash balance (all-time)"""
    try:
        cash_in_transactions = CashTransaction.objects(transaction_type='in')
        cash_out_transactions = CashTransaction.objects(transaction_type='out')
        
        cash_in = sum([float(t.amount) for t in cash_in_transactions]) if cash_in_transactions else 0.0
        cash_out = sum([float(t.amount) for t in cash_out_transactions]) if cash_out_transactions else 0.0

        balance = cash_in - cash_out

        return jsonify({
            'balance': balance,
            'total_cash_in': cash_in,
            'total_cash_out': cash_out
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
