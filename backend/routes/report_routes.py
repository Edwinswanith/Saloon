from flask import Blueprint, request, jsonify
from models import Bill, Service, ServiceGroup, Staff, Customer, Expense, Product, PrepaidPackage, Membership
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch
from utils.date_utils import get_ist_date_range

report_bp = Blueprint('report', __name__)

def get_safe_customer_info(customer_ref):
    """Safely extract customer info, handling deleted references"""
    if not customer_ref:
        return {'name': 'Walk-in', 'mobile': None, 'id': None}
    
    try:
        # Try to reload if it's a DBRef
        if hasattr(customer_ref, 'reload'):
            try:
                customer_ref.reload()
            except:
                # Customer deleted, return default
                return {'name': 'Walk-in', 'mobile': None, 'id': None}
        
        # Check if customer has required attributes
        if hasattr(customer_ref, 'first_name'):
            return {
                'name': f"{customer_ref.first_name or ''} {customer_ref.last_name or ''}".strip() or 'Walk-in',
                'mobile': getattr(customer_ref, 'mobile', None),
                'id': str(customer_ref.id) if hasattr(customer_ref, 'id') else None
            }
    except Exception:
        pass
    
    return {'name': 'Walk-in', 'mobile': None, 'id': None}

@report_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@report_bp.route('/service-sales-analysis', methods=['GET'])
@require_role('manager', 'owner')
def service_sales_analysis(current_user=None):
    """Service performance analysis report (Manager and Owner only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        service_group = request.args.get('service_group')  # Add service group filter parameter

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        bills_query = Bill.objects(is_deleted=False)
        if branch:
            bills_query = bills_query.filter(branch=branch)

        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)

        # Force evaluation by converting to list
        bills = list(bills_query)

        # Group by service
        service_stats = {}
        for bill in bills:
            for item in bill.items:
                if item.item_type == 'service' and item.service:
                    try:
                        # Reload service to ensure it's dereferenced
                        item.service.reload()
                        service_id = str(item.service.id)
                        
                        # Get service group name
                        service_group_name = None
                        if hasattr(item.service, 'group') and item.service.group:
                            try:
                                item.service.group.reload()
                                service_group_name = item.service.group.name if hasattr(item.service.group, 'name') else None
                            except (DoesNotExist, AttributeError):
                                pass
                        
                        # Filter by service group if specified
                        if service_group and service_group != 'all':
                            if not service_group_name or service_group_name.lower() != service_group.lower():
                                continue
                        
                        if service_id not in service_stats:
                            service_stats[service_id] = {
                                'service_name': item.service.name if hasattr(item.service, 'name') else 'Unknown Service',
                                'service_group': service_group_name,
                                'count': 0,
                                'revenue': 0
                            }
                        
                        service_stats[service_id]['count'] += int(item.quantity) if item.quantity else 0
                        service_stats[service_id]['revenue'] += float(item.total) if item.total else 0.0
                    except (DoesNotExist, AttributeError, TypeError) as e:
                        # Skip items with broken references
                        continue

        # Convert to list and sort by revenue
        results = sorted(service_stats.values(), key=lambda x: x['revenue'], reverse=True)

        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/list-of-bills', methods=['GET'])
@require_role('manager', 'owner')
def list_of_bills(current_user=None):
    """Bills list report with date range (Manager and Owner only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id', type=str)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Bill.objects(is_deleted=False)
        if branch:
            query = query.filter(branch=branch)

        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                query = query.filter(bill_date__gte=start)
            if end:
                query = query.filter(bill_date__lte=end)
        if customer_id and ObjectId.is_valid(customer_id):
            try:
                customer = Customer.objects.get(id=customer_id)
                query = query.filter(customer=customer)
            except DoesNotExist:
                pass

        # Force evaluation by converting to list
        bills = list(query.order_by('-bill_date'))

        result = []
        for b in bills:
            try:
                # Format bill_date to show local date correctly
                bill_date_iso = b.bill_date.isoformat() if b.bill_date else None
                customer_info = get_safe_customer_info(b.customer)
                result.append({
                    'bill_number': b.bill_number,
                    'bill_date': bill_date_iso,
                    'customer_name': customer_info['name'],
                    'customer_mobile': customer_info['mobile'],
                    'customer_id': customer_info['id'],
                    'id': str(b.id),
                    'subtotal': b.subtotal,
                    'discount': b.discount_amount,
                    'tax': b.tax_amount,
                    'final_amount': b.final_amount,
                    'payment_mode': b.payment_mode,
                    'booking_status': b.booking_status
                })
            except Exception as e:
                print(f"Error processing bill {b.id}: {e}")
                continue
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/deleted-bills', methods=['GET'])
@require_role('manager', 'owner')
def deleted_bills_report(current_user=None):
    """Deleted bills report with reasons (Manager and Owner only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Bill.objects(is_deleted=True)
        if branch:
            query = query.filter(branch=branch)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(deleted_at__gte=start)
        if end_date:
            # Set end_date to end of day to include all bills on that date
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(deleted_at__lte=end)

        # Force evaluation by converting to list
        bills = list(query.order_by('-deleted_at'))

        result = []
        for b in bills:
            try:
                customer_info = get_safe_customer_info(b.customer)
                result.append({
                    'bill_number': b.bill_number,
                    'bill_date': b.bill_date.isoformat() if b.bill_date else None,
                    'deleted_at': b.deleted_at.isoformat() if b.deleted_at else None,
                    'customer_name': customer_info['name'],
                    'final_amount': b.final_amount,
                    'deletion_reason': b.deletion_reason
                })
            except Exception as e:
                print(f"Error processing deleted bill {b.id}: {e}")
                continue
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/sales-by-service-group', methods=['GET'])
@require_role('manager', 'owner')
def sales_by_service_group(current_user=None):
    """Sales grouped by service group (Manager and Owner only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        bills_query = Bill.objects(is_deleted=False)
        if branch:
            bills_query = bills_query.filter(branch=branch)

        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)

        # Force evaluation by converting to list
        bills = list(bills_query)

        # Group by service group
        group_stats = {}
        for bill in bills:
            for item in bill.items:
                if item.item_type == 'service' and item.service and item.service.group:
                    group_name = item.service.group.name
                    if group_name not in group_stats:
                        group_stats[group_name] = {
                            'count': 0,
                            'revenue': 0.0
                        }
                    group_stats[group_name]['count'] += int(item.quantity) if item.quantity else 0
                    group_stats[group_name]['revenue'] += float(item.total) if item.total else 0.0

        total_revenue = sum([stats['revenue'] for stats in group_stats.values()])

        results = [{
            'group_name': name,
            'count': stats['count'],
            'revenue': round(stats['revenue'], 2),
            'percentage': round((stats['revenue'] / total_revenue * 100) if total_revenue > 0 else 0, 2)
        } for name, stats in group_stats.items()]
        
        # Sort by revenue
        results.sort(key=lambda x: x['revenue'], reverse=True)

        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/prepaid-clients', methods=['GET'])
@require_role('manager', 'owner')
def prepaid_clients_report(current_user=None):
    """Active prepaid package clients (Manager and Owner only)"""
    try:
        status = request.args.get('status', 'active')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        packages = PrepaidPackage.objects(status=status)
        if branch:
            packages = packages.filter(branch=branch)
        packages = packages.order_by('-purchase_date')

        response = jsonify([{
            'customer_name': f"{p.customer.first_name} {p.customer.last_name}" if p.customer else None,
            'customer_mobile': p.customer.mobile if p.customer else None,
            'package_name': p.name,
            'group_name': p.group.name if p.group else None,
            'price': p.price,
            'remaining_balance': p.remaining_balance,
            'purchase_date': p.purchase_date.isoformat() if p.purchase_date else None,
            'expiry_date': p.expiry_date.isoformat() if p.expiry_date else None,
            'usage_percentage': round(((p.price - p.remaining_balance) / p.price * 100) if p.price > 0 else 0, 2)
        } for p in packages])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/membership-clients', methods=['GET'])
@require_role('manager', 'owner')
def membership_clients_report(current_user=None):
    """Active membership clients (Manager and Owner only)"""
    try:
        status = request.args.get('status', 'active')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        memberships_query = Membership.objects(status=status)
        if branch:
            memberships_query = memberships_query.filter(branch=branch)
        # Force evaluation by converting to list
        memberships = list(memberships_query.order_by('-purchase_date'))

        response = jsonify([{
            'customer_name': f"{m.customer.first_name} {m.customer.last_name}" if m.customer else None,
            'customer_mobile': m.customer.mobile if m.customer else None,
            'membership_name': m.name,
            'price': m.price,
            'purchase_date': m.purchase_date.isoformat() if m.purchase_date else None,
            'expiry_date': m.expiry_date.isoformat() if m.expiry_date else None,
            'days_remaining': (m.expiry_date - datetime.now()).days if m.expiry_date and m.expiry_date > datetime.now() else 0,
            'plan': {
                'allocated_discount': m.plan.allocated_discount if m.plan else 0
            } if m.plan else None
        } for m in memberships])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/staff-incentive', methods=['GET'])
@require_role('manager', 'owner')
def staff_incentive_report(current_user=None):
    """Staff commission/incentive report with breakdown by item type (Manager and Owner only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        staff_query = Staff.objects(status='active')
        if branch:
            staff_query = staff_query.filter(branch=branch)
        # Force evaluation by converting to list
        staff_list = list(staff_query)

        report = []
        for staff in staff_list:
            bills_query = Bill.objects(is_deleted=False)
            if branch:
                bills_query = bills_query.filter(branch=branch)

            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                bills_query = bills_query.filter(bill_date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                # Set end to end of day to include all data from the end date
                end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                bills_query = bills_query.filter(bill_date__lte=end)

            # Force evaluation by converting to list
            bills = list(bills_query)

            # Breakdown by item type
            service_revenue = 0.0
            package_revenue = 0.0
            product_revenue = 0.0
            prepaid_revenue = 0.0
            membership_revenue = 0.0
            total_revenue = 0.0
            item_count = 0

            for bill in bills:
                for item in bill.items:
                    if item.staff and str(item.staff.id) == str(staff.id):
                        item_total = float(item.total) if item.total else 0.0
                        total_revenue += item_total
                        item_count += 1
                        
                        if item.item_type == 'service':
                            service_revenue += item_total
                        elif item.item_type == 'package':
                            package_revenue += item_total
                        elif item.item_type == 'product':
                            product_revenue += item_total
                        elif item.item_type == 'prepaid':
                            prepaid_revenue += item_total
                        elif item.item_type == 'membership':
                            membership_revenue += item_total
            
            avg_bill = total_revenue / item_count if item_count > 0 else 0
            commission = total_revenue * (staff.commission_rate / 100) if staff.commission_rate else 0

            report.append({
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'item_count': item_count,
                'service': round(service_revenue, 2),
                'package': round(package_revenue, 2),
                'product': round(product_revenue, 2),
                'prepaid': round(prepaid_revenue, 2),
                'membership': round(membership_revenue, 2),
                'total': round(total_revenue, 2),
                'avg_bill': round(avg_bill, 2),
                'total_revenue': round(total_revenue, 2),
                'commission_rate': staff.commission_rate,
                'commission_earned': round(commission, 2),
                'salary': staff.salary,
                'total_earnings': round((staff.salary or 0) + commission, 2)
            })

        # Sort by total revenue
        report.sort(key=lambda x: x['total_revenue'], reverse=True)

        response = jsonify(report)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/expense-report', methods=['GET'])
@require_role('manager', 'owner')
def expense_report(current_user=None):
    """Expense report with filters"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_id = request.args.get('category_id', type=str)
        payment_mode = request.args.get('payment_mode')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Expense.objects
        if branch:
            query = query.filter(branch=branch)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(expense_date__lte=end)
        if category_id and ObjectId.is_valid(category_id):
            try:
                from models import ExpenseCategory
                category = ExpenseCategory.objects.get(id=category_id)
                query = query.filter(category=category)
            except DoesNotExist:
                pass
        if payment_mode:
            query = query.filter(payment_mode=payment_mode)

        # Force evaluation by converting to list
        expenses = list(query.order_by('-expense_date'))

        total = sum([float(e.amount) for e in expenses])

        response = jsonify({
            'expenses': [{
                'date': e.expense_date.isoformat() if e.expense_date else None,
                'category': e.category.name if e.category else None,
                'name': e.name,
                'amount': e.amount,
                'payment_mode': e.payment_mode,
                'description': e.description
            } for e in expenses],
            'total_expenses': round(total, 2),
            'count': len(list(expenses))
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/inventory-report', methods=['GET'])
def inventory_report():
    """Stock levels and low stock items"""
    try:
        category_id = request.args.get('category_id', type=str)
        low_stock_only = request.args.get('low_stock_only', type=bool, default=False)

        query = Product.objects(status='active')

        if category_id and ObjectId.is_valid(category_id):
            try:
                from models import ProductCategory
                category = ProductCategory.objects.get(id=category_id)
                query = query.filter(category=category)
            except DoesNotExist:
                pass

        products = list(query.order_by('stock_quantity'))
        
        # Filter low stock in Python (MongoEngine doesn't support field comparison)
        if low_stock_only:
            products = [p for p in products if p.stock_quantity and p.min_stock_level and p.stock_quantity <= p.min_stock_level]

        total_stock_value = sum([(p.stock_quantity or 0) * (p.cost or 0) for p in products])
        low_stock_count = len([p for p in products if p.stock_quantity and p.min_stock_level and p.stock_quantity <= p.min_stock_level])

        response = jsonify({
            'products': [{
                'name': p.name,
                'category': p.category.name if p.category else None,
                'stock_quantity': p.stock_quantity,
                'min_stock_level': p.min_stock_level,
                'cost': p.cost,
                'price': p.price,
                'stock_value': (p.stock_quantity or 0) * (p.cost or 0),
                'status': 'Low Stock' if (p.stock_quantity and p.min_stock_level and p.stock_quantity <= p.min_stock_level) else 'In Stock'
            } for p in products],
            'summary': {
                'total_products': len(products),
                'low_stock_items': low_stock_count,
                'total_stock_value': round(total_stock_value, 2)
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/staff-combined', methods=['GET'])
def staff_combined_report():
    """Combined staff performance and bill report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        staff_id = request.args.get('staff_id')

        query = Bill.objects.filter(is_deleted=False)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(bill_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end to end of day to include all data from the end date
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(bill_date__lte=end)

        # Force evaluation by converting to list
        bills = list(query)

        # Group by staff
        staff_data = {}
        for bill in bills:
            for item in (bill.items or []):
                if not item.staff:
                    continue
                
                item_staff_id = str(item.staff.id)
                
                # Filter by staff_id if provided
                if staff_id and item_staff_id != staff_id:
                    continue
                
                if item_staff_id not in staff_data:
                    staff_data[item_staff_id] = {
                        'staff_name': f"{item.staff.first_name} {item.staff.last_name}" if hasattr(item.staff, 'first_name') else 'Unknown',
                        'services_count': 0,
                        'revenue': 0,
                        'services': []
                    }

                staff_data[item_staff_id]['services_count'] += 1
                staff_data[item_staff_id]['revenue'] += item.total or 0

                if item.service:
                    staff_data[item_staff_id]['services'].append({
                        'service_name': item.service.name if hasattr(item.service, 'name') else 'Unknown',
                        'bill_number': bill.bill_number,
                        'date': bill.bill_date.isoformat() if isinstance(bill.bill_date, datetime) else str(bill.bill_date),
                        'amount': item.total or 0
                    })

        results = sorted(staff_data.values(), key=lambda x: x['revenue'], reverse=True)

        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/business-growth', methods=['GET'])
def business_growth_report():
    """Business growth and trend analysis"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            start_date = (datetime.now().replace(day=1) - timedelta(days=90)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        # Set end to end of day to include all data from the end date
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get all bills in date range - force evaluation
        bills = list(Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        ))

        # Group bills by month
        monthly_revenue = {}
        for bill in bills:
            month_key = bill.bill_date.strftime('%Y-%m')
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = {'revenue': 0, 'bills': 0}
            monthly_revenue[month_key]['revenue'] += bill.final_amount or 0
            monthly_revenue[month_key]['bills'] += 1

        # Get all expenses in date range - force evaluation
        expenses = list(Expense.objects.filter(
            expense_date__gte=start.date(),
            expense_date__lte=end.date()
        ))

        # Group expenses by month
        monthly_expenses = {}
        for expense in expenses:
            if expense.expense_date:
                month_key = expense.expense_date.strftime('%Y-%m')
                if month_key not in monthly_expenses:
                    monthly_expenses[month_key] = 0
                monthly_expenses[month_key] += expense.amount or 0

        # Combine data
        growth_data = []
        for month in sorted(monthly_revenue.keys()):
            revenue_data = monthly_revenue[month]
            expenses = monthly_expenses.get(month, 0)
            profit = revenue_data['revenue'] - expenses

            growth_data.append({
                'month': month,
                'revenue': round(revenue_data['revenue'], 2),
                'expenses': round(expenses, 2),
                'profit': round(profit, 2),
                'bills': revenue_data['bills']
            })

        response = jsonify(growth_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/staff-performance', methods=['GET'])
def staff_performance_analysis():
    """Staff performance analysis"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Force evaluation by converting to list
        try:
            staff_list = list(Staff.objects.filter(status='active'))
        except Exception as e:
            print(f"Error fetching staff list: {str(e)}")
            staff_list = []

        # Build date filter for bills
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = datetime.now() - timedelta(days=90)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end to end of day to include all data from the end date
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            end = datetime.now()

        # Get all bills in date range - force evaluation
        bills = list(Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        ))

        performance = []
        for staff in staff_list:
            try:
                staff_id = str(staff.id)

                # Calculate breakdown by item type
                service_revenue = 0
                package_revenue = 0
                prepaid_revenue = 0
                product_revenue = 0
                membership_revenue = 0
                total_revenue = 0
                item_count = 0

                # Group by service type for service breakdown
                service_breakdown = {}

                # Filter items for this staff
                for bill in bills:
                    if not bill.items:
                        continue
                    for item in bill.items:
                        if not item:
                            continue
                        # Handle staff reference - could be ObjectId, ReferenceField, or None
                        item_staff_id = None
                        try:
                            if item.staff:
                                # If it's a ReferenceField, get the ID
                                if hasattr(item.staff, 'id'):
                                    item_staff_id = str(item.staff.id)
                                # If it's already an ObjectId or string
                                elif isinstance(item.staff, (str, ObjectId)):
                                    item_staff_id = str(item.staff)
                                # Try to get ID from the object
                                else:
                                    item_staff_id = str(getattr(item.staff, 'id', item.staff))
                        except Exception as e:
                            # If we can't get staff ID, skip this item
                            continue

                        if not item_staff_id or item_staff_id != staff_id:
                            continue

                        item_type = item.item_type or 'service'
                        item_count += item.quantity if item.quantity else 1
                        total_revenue += float(item.total) if item.total else 0.0

                        if item_type == 'service':
                            service_revenue += float(item.total) if item.total else 0.0
                            # Try to access service, but handle case where service was deleted
                            group_name = 'Other'
                            try:
                                # Check if service reference exists in raw data first
                                has_service_ref = False
                                if hasattr(item, '_data') and 'service' in item._data:
                                    has_service_ref = item._data['service'] is not None

                                # Only try to access service if reference exists
                                if has_service_ref:
                                    try:
                                        # Access service - this may raise DoesNotExist if service was deleted
                                        service_obj = item.service
                                        if service_obj:
                                            # Reload service to get group
                                            if hasattr(service_obj, 'reload'):
                                                service_obj.reload()
                                            # Safely access group name
                                            if hasattr(service_obj, 'group') and service_obj.group:
                                                if hasattr(service_obj.group, 'name') and service_obj.group.name:
                                                    group_name = service_obj.group.name
                                    except DoesNotExist:
                                        # Service was deleted, use 'Other'
                                        group_name = 'Other'
                                    except (AttributeError, Exception):
                                        # Any other error accessing service/group, use 'Other'
                                        group_name = 'Other'
                            except Exception:
                                # Any error, use 'Other'
                                group_name = 'Other'

                            if group_name not in service_breakdown:
                                service_breakdown[group_name] = {'count': 0, 'revenue': 0}
                            service_breakdown[group_name]['count'] += item.quantity if item.quantity else 1
                            service_breakdown[group_name]['revenue'] += float(item.total) if item.total else 0.0
                        elif item_type == 'package':
                            package_revenue += float(item.total) if item.total else 0.0
                        elif item_type == 'prepaid':
                            prepaid_revenue += float(item.total) if item.total else 0.0
                        elif item_type == 'product':
                            product_revenue += float(item.total) if item.total else 0.0
                        elif item_type == 'membership':
                            membership_revenue += float(item.total) if item.total else 0.0

                performance.append({
                    'staff_name': f"{staff.first_name or ''} {staff.last_name or ''}".strip(),
                    'total_revenue': round(float(total_revenue), 2),
                    'total_services': int(item_count),
                    'service_revenue': round(float(service_revenue), 2),
                    'package_revenue': round(float(package_revenue), 2),
                    'prepaid_revenue': round(float(prepaid_revenue), 2),
                    'product_revenue': round(float(product_revenue), 2),
                    'membership_revenue': round(float(membership_revenue), 2),
                    'service_breakdown': service_breakdown,
                    'average_per_service': round(float(total_revenue) / item_count, 2) if item_count > 0 else 0
                })
            except Exception as staff_error:
                # If processing one staff fails, log and continue with next staff
                print(f"Error processing staff {getattr(staff, 'id', 'unknown')}: {str(staff_error)}")
                import traceback
                print(traceback.format_exc())
                continue

        performance.sort(key=lambda x: x['total_revenue'], reverse=True)

        response = jsonify(performance)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in staff_performance_analysis: {str(e)}")
        print(f"Traceback: {error_trace}")
        response = jsonify({'error': str(e), 'traceback': error_trace})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@report_bp.route('/period-summary', methods=['GET'])
def period_summary():
    """Period performance summary"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            response = jsonify({'error': 'start_date and end_date are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        # Set end to end of day to include all data from the end date
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Revenue - force evaluation
        bills = list(Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        ))
        total_revenue = sum(bill.final_amount or 0 for bill in bills)
        total_bills = len(bills)

        # Expenses - force evaluation
        expenses = list(Expense.objects.filter(
            expense_date__gte=start.date(),
            expense_date__lte=end.date()
        ))
        total_expenses = sum(expense.amount or 0 for expense in expenses)

        # Profit
        profit = total_revenue - total_expenses

        # Customers served
        customer_ids = set()
        for bill in bills:
            if bill.customer:
                customer_ids.add(str(bill.customer.id))
        customers_served = len(customer_ids)

        # Appointments
        appointments = Appointment.objects.filter(
            appointment_date__gte=start.date(),
            appointment_date__lte=end.date()
        ).count()

        response = jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'average_per_bill': round(total_revenue / total_bills, 2) if total_bills > 0 else 0
            },
            'bills': {
                'total': total_bills
            },
            'expenses': {
                'total': round(total_expenses, 2)
            },
            'profit': {
                'total': round(profit, 2),
                'margin': round((profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
            },
            'customers': {
                'served': customers_served
            },
            'appointments': {
                'total': appointments
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
