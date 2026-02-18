from flask import Blueprint, request, jsonify
from models import CashTransaction
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch

cash_bp = Blueprint('cash', __name__)

@cash_bp.route('/transactions', methods=['GET'])
@require_auth
def get_cash_transactions(current_user=None):
    """Get cash transactions with optional filters"""
    try:
        # Query parameters
        transaction_type = request.args.get('transaction_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_param = request.args.get('date')  # Single date filter (for daily view)

        query = CashTransaction.objects

        # Branch filter
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        # Apply type filter
        if transaction_type:
            query = query.filter(transaction_type=transaction_type)

        # Handle single date filter (for daily view)
        if date_param:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
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
                'transaction_time': t.transaction_time if t.transaction_time else None,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/transactions/<id>', methods=['GET'])
@require_auth
def get_cash_transaction(id, current_user=None):
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
            'transaction_time': transaction.transaction_time if transaction.transaction_time else None,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/in', methods=['POST'])
@require_auth
def add_cash_in(current_user=None):
    """Add cash in transaction"""
    try:
        data = request.get_json()

        branch = get_selected_branch(request, current_user)

        transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date() if 'transaction_date' in data else date.today()
        transaction_time = data.get('transaction_time', datetime.now().strftime('%H:%M:%S'))
        if isinstance(transaction_time, str):
            if '.' in transaction_time:
                transaction_time = transaction_time.split('.')[0]
        else:
            transaction_time = transaction_time.strftime('%H:%M:%S') if hasattr(transaction_time, 'strftime') else str(transaction_time)

        transaction = CashTransaction(
            transaction_type='in',
            branch=branch,
            amount=data['amount'],
            reason=data.get('reason'),
            notes=data.get('notes'),
            transaction_date=transaction_date,
            transaction_time=transaction_time
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
@require_auth
def add_cash_out(current_user=None):
    """Add cash out transaction"""
    try:
        data = request.get_json()

        branch = get_selected_branch(request, current_user)

        transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date() if 'transaction_date' in data else date.today()
        transaction_time = data.get('transaction_time', datetime.now().strftime('%H:%M:%S'))
        if isinstance(transaction_time, str):
            if '.' in transaction_time:
                transaction_time = transaction_time.split('.')[0]
        else:
            transaction_time = transaction_time.strftime('%H:%M:%S') if hasattr(transaction_time, 'strftime') else str(transaction_time)

        transaction = CashTransaction(
            transaction_type='out',
            branch=branch,
            amount=data['amount'],
            reason=data.get('reason'),
            notes=data.get('notes'),
            transaction_date=transaction_date,
            transaction_time=transaction_time
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
@require_auth
def update_cash_transaction(id, current_user=None):
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

        if 'transaction_date' in data:
            transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        if 'transaction_time' in data:
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
@require_role('manager', 'owner')
def delete_cash_transaction(id, current_user=None):
    """Delete a cash transaction (Manager and Owner only)"""
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
@require_auth
def get_cash_summary(current_user=None):
    """Get cash flow summary"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_param = request.args.get('date')

        query = CashTransaction.objects

        # Branch filter
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        if date_param:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
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
            'cash_in': cash_in,
            'cash_out': cash_out,
            'net_cash': net_cash,
            'total_transactions': len(transactions),
            'in_transactions': len([t for t in transactions if t.transaction_type == 'in']),
            'out_transactions': len([t for t in transactions if t.transaction_type == 'out'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cash_bp.route('/daily-summary', methods=['GET'])
@require_auth
def get_daily_cash_summary(current_user=None):
    """Get daily cash summary grouped by date"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = CashTransaction.objects

        # Branch filter
        branch = get_selected_branch(request, current_user)
        if branch:
            query = query.filter(branch=branch)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(transaction_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(transaction_date__lte=end)

        transactions = list(query)

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
@require_auth
def get_cash_balance(current_user=None):
    """Get current cash balance"""
    try:
        query_in = CashTransaction.objects(transaction_type='in')
        query_out = CashTransaction.objects(transaction_type='out')

        # Branch filter
        branch = get_selected_branch(request, current_user)
        if branch:
            query_in = query_in.filter(branch=branch)
            query_out = query_out.filter(branch=branch)

        cash_in = sum([float(t.amount) for t in query_in]) if query_in else 0.0
        cash_out = sum([float(t.amount) for t in query_out]) if query_out else 0.0
        balance = cash_in - cash_out

        return jsonify({
            'balance': balance,
            'total_cash_in': cash_in,
            'total_cash_out': cash_out
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
