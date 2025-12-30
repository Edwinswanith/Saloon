from flask import Blueprint, request, jsonify
from models import Expense, ExpenseCategory
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth, require_role

expense_bp = Blueprint('expense', __name__)

@expense_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Expense Category Routes

@expense_bp.route('/categories', methods=['GET'])
def get_expense_categories():
    """Get all expense categories"""
    try:
        categories = ExpenseCategory.objects.order_by('name')
        response = jsonify([{
            'id': str(cat.id),
            'name': cat.name,
            'description': cat.description,
            'created_at': cat.created_at.isoformat() if cat.created_at else None
        } for cat in categories])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/categories', methods=['POST'])
@require_role('manager', 'owner')
def create_expense_category(current_user=None):
    """Create a new expense category (Manager and Owner only)"""
    try:
        data = request.get_json()

        category = ExpenseCategory(
            name=data['name'],
            description=data.get('description')
        )
        category.save()

        response = jsonify({
            'id': str(category.id),
            'message': 'Expense category created successfully',
            'data': {
                'id': str(category.id),
                'name': category.name
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/categories/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_expense_category(id, current_user=None):
    """Update an expense category (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid category ID format'}), 400
        
        category = ExpenseCategory.objects.get(id=id)
        data = request.get_json()

        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        category.save()

        response = jsonify({
            'id': str(category.id),
            'message': 'Expense category updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Expense category not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/categories/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_expense_category(id, current_user=None):
    """Delete an expense category (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid category ID format'}), 400
        
        category = ExpenseCategory.objects.get(id=id)

        # Check if category has expenses
        expense_count = Expense.objects(category=category).count()
        if expense_count > 0:
            response = jsonify({'error': 'Cannot delete category with associated expenses'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        category.delete()

        response = jsonify({'message': 'Expense category deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Expense category not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Expense Routes

@expense_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_expenses(current_user=None):
    """Get all expenses with optional filters (Manager and Owner only)"""
    try:
        # Query parameters
        category_id = request.args.get('category_id')
        payment_mode = request.args.get('payment_mode')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Expense.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if category_id:
            if ObjectId.is_valid(category_id):
                query = query.filter(category=ObjectId(category_id))
        if payment_mode:
            query = query.filter(payment_mode=payment_mode)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__lte=end)
        if search:
            query = query.filter(name__icontains=search)

        expenses = query.order_by('-expense_date')

        response = jsonify([{
            'id': str(e.id),
            'name': e.name,
            'category_id': str(e.category.id) if e.category else None,
            'category_name': e.category.name if e.category else None,
            'amount': e.amount,
            'payment_mode': e.payment_mode,
            'expense_date': e.expense_date.isoformat() if e.expense_date else None,
            'description': e.description,
            'created_at': e.created_at.isoformat() if e.created_at else None
        } for e in expenses])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/<id>', methods=['GET'])
@require_auth
def get_expense(id, current_user=None):
    """Get a single expense by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid expense ID format'}), 400
        
        expense = Expense.objects.get(id=id)
        response = jsonify({
            'id': str(expense.id),
            'name': expense.name,
            'category_id': str(expense.category.id) if expense.category else None,
            'category_name': expense.category.name if expense.category else None,
            'amount': expense.amount,
            'payment_mode': expense.payment_mode,
            'expense_date': expense.expense_date.isoformat() if expense.expense_date else None,
            'description': expense.description,
            'created_at': expense.created_at.isoformat() if expense.created_at else None,
            'updated_at': expense.updated_at.isoformat() if expense.updated_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Expense not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_expense(current_user=None):
    """Create a new expense (Manager and Owner only)"""
    try:
        data = request.get_json()

        # Parse expense date
        expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()

        # Get category reference
        category_id = data.get('category_id')
        if not category_id or not ObjectId.is_valid(category_id):
            return jsonify({'error': 'Invalid category ID format'}), 400
        
        try:
            category = ExpenseCategory.objects.get(id=category_id)
        except DoesNotExist:
            return jsonify({'error': 'Expense category not found'}), 404

        expense = Expense(
            name=data['name'],
            category=category,
            branch=branch,
            amount=data['amount'],
            payment_mode=data.get('payment_mode'),
            expense_date=expense_date,
            description=data.get('description')
        )
        expense.save()

        response = jsonify({
            'id': str(expense.id),
            'message': 'Expense created successfully',
            'data': {
                'id': str(expense.id),
                'name': expense.name,
                'amount': expense.amount
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_expense(id, current_user=None):
    """Update an expense (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid expense ID format'}), 400
        
        expense = Expense.objects.get(id=id)
        data = request.get_json()

        expense.name = data.get('name', expense.name)
        expense.amount = data.get('amount', expense.amount)
        expense.payment_mode = data.get('payment_mode', expense.payment_mode)

        # Update category if provided
        if 'category_id' in data:
            category_id = data['category_id']
            if category_id and ObjectId.is_valid(category_id):
                try:
                    expense.category = ExpenseCategory.objects.get(id=category_id)
                except DoesNotExist:
                    return jsonify({'error': 'Expense category not found'}), 404

        # Update expense date if provided
        if 'expense_date' in data:
            expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()

        expense.description = data.get('description', expense.description)
        expense.updated_at = datetime.utcnow()
        expense.save()

        response = jsonify({
            'id': str(expense.id),
            'message': 'Expense updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Expense not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_expense(id, current_user=None):
    """Delete an expense (Manager and Owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid expense ID format'}), 400
        
        expense = Expense.objects.get(id=id)
        expense.delete()

        response = jsonify({'message': 'Expense deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Expense not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/summary', methods=['GET'])
def get_expense_summary():
    """Get expense summary by category for a date range"""
    try:
        # Query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Expense.objects

        # Apply date filters
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__lte=end)

        # Get all expenses and group by category
        expenses = list(query)
        category_totals = {}
        
        for expense in expenses:
            if expense.category:
                cat_name = expense.category.name
                if cat_name not in category_totals:
                    category_totals[cat_name] = {'total_amount': 0, 'count': 0}
                category_totals[cat_name]['total_amount'] += expense.amount or 0
                category_totals[cat_name]['count'] += 1

        total = sum(cat['total_amount'] for cat in category_totals.values())

        response = jsonify({
            'summary': [{
                'category_name': cat_name,
                'total_amount': cat_data['total_amount'],
                'count': cat_data['count'],
                'percentage': (cat_data['total_amount'] / total * 100) if total > 0 else 0
            } for cat_name, cat_data in category_totals.items()],
            'grand_total': total
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@expense_bp.route('/total', methods=['GET'])
def get_total_expenses():
    """Get total expenses for a date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Expense.objects

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__lte=end)

        expenses = list(query)
        total = sum(e.amount or 0 for e in expenses)

        response = jsonify({'total': total})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
