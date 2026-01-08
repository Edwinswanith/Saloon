from flask import Blueprint, request, jsonify
from models import Bill, Customer, Staff, Expense, Product, Appointment, Lead, Feedback
from datetime import datetime, timedelta, date
from mongoengine import Q
from mongoengine.errors import DoesNotExist
from utils.auth import require_auth
from utils.branch_filter import get_selected_branch, filter_by_branch
from utils.date_utils import get_ist_date_range, ist_to_utc_start, ist_to_utc_end, get_ist_today

dashboard_bp = Blueprint('dashboard', __name__)

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

@dashboard_bp.route('/stats', methods=['GET'])
@require_auth
def get_dashboard_stats(current_user=None):
    """Get overall dashboard statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Default to last 30 days if no date range provided (using IST)
        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Total revenue from bills - force evaluation by converting to list
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        bills = list(bills_query)  # Force evaluation
        total_revenue = sum([float(b.final_amount) for b in bills]) if bills else 0.0

        # Total transactions (bills)
        total_transactions = len(bills)

        # Total expenses - force evaluation by converting to list
        # Note: expense_date is a DateField, so we use IST dates directly
        # Convert IST date strings to date objects for DateField filtering
        ist_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        ist_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        expenses_query = Expense.objects(
            expense_date__gte=ist_start_date,
            expense_date__lte=ist_end_date
        )
        if branch:
            expenses_query = expenses_query.filter(branch=branch)
        expenses = list(expenses_query)  # Force evaluation
        total_expenses = sum([float(e.amount) for e in expenses]) if expenses else 0.0

        # Net profit
        net_profit = float(total_revenue) - float(total_expenses)

        # Average bill value
        avg_bill_value = float(total_revenue) / int(total_transactions) if total_transactions > 0 else 0.0

        # Total customers
        customers_query = Customer.objects
        if branch:
            customers_query = customers_query.filter(branch=branch)
        total_customers = customers_query.count()

        # New customers in period - ensure end includes full day
        new_customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            new_customers_query = new_customers_query.filter(branch=branch)
        new_customers = new_customers_query.count()

        # Total staff
        staff_query = Staff.objects(status='active')
        if branch:
            staff_query = staff_query.filter(branch=branch)
        active_staff = staff_query.count()

        # Appointments stats
        # Note: appointment_date is a DateField, so we use IST dates directly
        total_appointments = Appointment.objects(
            appointment_date__gte=ist_start_date,
            appointment_date__lte=ist_end_date
        ).count()

        completed_appointments = Appointment.objects(
            appointment_date__gte=ist_start_date,
            appointment_date__lte=ist_end_date,
            status='completed'
        ).count()

        return jsonify({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'average_per_transaction': round(avg_bill_value, 2)
            },
            'transactions': {
                'total': total_transactions
            },
            'expenses': {
                'total': round(total_expenses, 2)
            },
            'profit': {
                'net': round(net_profit, 2),
                'margin': round((float(net_profit) / float(total_revenue) * 100) if total_revenue > 0 else 0, 2)
            },
            'customers': {
                'total': total_customers,
                'new': new_customers
            },
            'staff': {
                'active': active_staff
            },
            'appointments': {
                'total': total_appointments,
                'completed': completed_appointments,
                'completion_rate': round((completed_appointments / total_appointments * 100) if total_appointments > 0 else 0, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/staff-performance', methods=['GET'])
@require_auth
def get_staff_performance(current_user=None):
    """Get staff performance metrics (filtered by selected branch)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        # Set end to end of day to include all data from the end date
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Get staff filtered by branch - force evaluation
        staff_list = list(filter_by_branch(Staff.objects(status='active'), branch))

        performance = []
        for staff in staff_list:
            # Get bills with items served by this staff (filtered by branch) - force evaluation
            bills = list(filter_by_branch(Bill.objects(
                is_deleted=False,
                bill_date__gte=start,
                bill_date__lte=end
            ), branch))
            
            total_revenue = 0.0
            total_services = 0
            service_count = 0
            package_count = 0
            product_count = 0
            prepaid_count = 0
            membership_count = 0
            
            for bill in bills:
                for item in bill.items:
                    if item.staff and str(item.staff.id) == str(staff.id):
                        item_type = item.item_type or 'service'
                        quantity = item.quantity if item.quantity else 1
                        total_revenue += float(item.total) if item.total else 0.0
                        total_services += quantity
                        
                        # Count by item type
                        if item_type == 'service':
                            service_count += quantity
                        elif item_type == 'package':
                            package_count += quantity
                        elif item_type == 'product':
                            product_count += quantity
                        elif item_type == 'prepaid':
                            prepaid_count += quantity
                        elif item_type == 'membership':
                            membership_count += quantity

            # Calculate commission
            commission = total_revenue * (staff.commission_rate / 100) if staff.commission_rate else 0

            # Get appointments completed
            completed_appointments = Appointment.objects(
                staff=staff,
                appointment_date__gte=start.date(),
                appointment_date__lte=end.date(),
                status='completed'
            ).count()

            performance.append({
                'staff_id': str(staff.id),
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'total_revenue': round(total_revenue, 2),
                'total_services': total_services,
                'service_count': service_count,
                'package_count': package_count,
                'product_count': product_count,
                'prepaid_count': prepaid_count,
                'membership_count': membership_count,
                'commission_earned': round(commission, 2),
                'completed_appointments': completed_appointments
            })

        # Sort by revenue
        performance.sort(key=lambda x: x['total_revenue'], reverse=True)

        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-customers', methods=['GET'])
@require_auth
def get_top_customers(current_user=None):
    """Get top 10 customers by revenue"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Get bills in date range - convert IST dates to UTC for filtering
        bills_query = Bill.objects(is_deleted=False)
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)
        
        # Group by customer
        customer_stats = {}
        for bill in bills:
            if bill.customer:
                customer_id = str(bill.customer.id)
                if customer_id not in customer_stats:
                    customer_stats[customer_id] = {
                        'customer': bill.customer,
                        'total_spent': 0.0,
                        'visit_count': 0
                    }
                customer_stats[customer_id]['total_spent'] += float(bill.final_amount) if bill.final_amount else 0.0
                customer_stats[customer_id]['visit_count'] += 1
        
        # Convert to list and sort
        results = sorted(customer_stats.values(), key=lambda x: x['total_spent'], reverse=True)[:limit]
        
        return jsonify([{
            'customer_id': str(r['customer'].id),
            'customer_name': f"{r['customer'].first_name} {r['customer'].last_name}",
            'mobile': r['customer'].mobile,
            'total_spent': round(r['total_spent'], 2),
            'visit_count': r['visit_count'],
            'average_per_visit': round(r['total_spent'] / r['visit_count'], 2) if r['visit_count'] > 0 else 0
        } for r in results])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-offerings', methods=['GET'])
@require_auth
def get_top_offerings(current_user=None):
    """Get top 10 services/products by revenue"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Get bills in date range - convert IST dates to UTC for filtering
        bills_query = Bill.objects(is_deleted=False)
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)

        # Group by service/product/package
        offerings = {}
        from models import Service, Product, Package
        
        for bill in bills:
            for item in (bill.items or []):
                try:
                    item_type = getattr(item, 'item_type', None)
                    if not item_type or item_type not in ['service', 'product', 'package']:
                        continue
                    
                    key = None
                    name = None
                    item_id = None

                    if item_type == 'service' and hasattr(item, 'service') and item.service:
                        try:
                            # Get service ID first
                            service_ref = item.service
                            if hasattr(service_ref, 'id'):
                                item_id = str(service_ref.id)
                            elif isinstance(service_ref, str):
                                item_id = service_ref
                            else:
                                continue
                            
                            # Try to reload if it's a DBRef
                            if hasattr(service_ref, 'reload'):
                                try:
                                    service_ref.reload()
                                    name = getattr(service_ref, 'name', None)
                                except:
                                    pass
                            
                            # If name not found, query Service collection directly
                            if not name:
                                try:
                                    service_obj = Service.objects(id=item_id).first()
                                    if service_obj:
                                        name = getattr(service_obj, 'name', 'Service')
                                    else:
                                        continue
                                except:
                                    continue
                            
                            key = f"service_{item_id}"
                        except (DoesNotExist, AttributeError, TypeError, ValueError) as e:
                            print(f"Error accessing service {item_id}: {e}")
                            continue
                            
                    elif item_type == 'product' and hasattr(item, 'product') and item.product:
                        try:
                            product_ref = item.product
                            if hasattr(product_ref, 'id'):
                                item_id = str(product_ref.id)
                            elif isinstance(product_ref, str):
                                item_id = product_ref
                            else:
                                continue
                            
                            if hasattr(product_ref, 'reload'):
                                try:
                                    product_ref.reload()
                                    name = getattr(product_ref, 'name', None)
                                except:
                                    pass
                            
                            if not name:
                                try:
                                    product_obj = Product.objects(id=item_id).first()
                                    if product_obj:
                                        name = getattr(product_obj, 'name', 'Product')
                                    else:
                                        continue
                                except:
                                    continue
                            
                            key = f"product_{item_id}"
                        except (DoesNotExist, AttributeError, TypeError, ValueError) as e:
                            print(f"Error accessing product {item_id}: {e}")
                            continue
                            
                    elif item_type == 'package' and hasattr(item, 'package') and item.package:
                        try:
                            package_ref = item.package
                            if hasattr(package_ref, 'id'):
                                item_id = str(package_ref.id)
                            elif isinstance(package_ref, str):
                                item_id = package_ref
                            else:
                                continue
                            
                            if hasattr(package_ref, 'reload'):
                                try:
                                    package_ref.reload()
                                    name = getattr(package_ref, 'name', None)
                                except:
                                    pass
                            
                            if not name:
                                try:
                                    package_obj = Package.objects(id=item_id).first()
                                    if package_obj:
                                        name = getattr(package_obj, 'name', 'Package')
                                    else:
                                        continue
                                except:
                                    continue
                            
                            key = f"package_{item_id}"
                        except (DoesNotExist, AttributeError, TypeError, ValueError) as e:
                            print(f"Error accessing package {item_id}: {e}")
                            continue

                    if key and name:
                        if key not in offerings:
                            offerings[key] = {
                                'name': name,
                                'type': item_type,
                                'revenue': 0.0,
                                'quantity': 0
                            }

                        offerings[key]['revenue'] += _safe_float(item.total)
                        offerings[key]['quantity'] += _safe_int(item.quantity)
                except (DoesNotExist, AttributeError, TypeError, ValueError) as e:
                    print(f"Error processing bill item: {e}")
                    continue

        # Convert to list and sort
        top_offerings = sorted(offerings.values(), key=lambda x: x['revenue'], reverse=True)[:limit]

        # Include offering IDs for client lookup
        result = []
        for o in top_offerings:
            # Find the offering ID from the original offerings dict
            offering_key = None
            for key, value in offerings.items():
                if value['name'] == o['name'] and value['type'] == o['type']:
                    offering_key = key
                    break
            
            result.append({
                'name': o['name'],
                'type': o['type'],
                'revenue': round(o['revenue'], 2),
                'quantity': o['quantity'],
                'key': offering_key  # Store key for client lookup
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/offering-clients', methods=['GET'])
@require_auth
def get_offering_clients(current_user=None):
    """Get customers who purchased a specific offering"""
    try:
        offering_name = request.args.get('name')
        offering_type = request.args.get('type')  # service, product, or package
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not offering_name or not offering_type:
            return jsonify({'error': 'Offering name and type are required'}), 400

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Get bills in date range
        bills_query = Bill.objects(is_deleted=False)
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        bills = list(bills_query)
        
        from models import Service, Product, Package
        
        # Find the offering ID
        offering_id = None
        if offering_type == 'service':
            service = Service.objects(name=offering_name).first()
            if service:
                offering_id = str(service.id)
        elif offering_type == 'product':
            product = Product.objects(name=offering_name).first()
            if product:
                offering_id = str(product.id)
        elif offering_type == 'package':
            package = Package.objects(name=offering_name).first()
            if package:
                offering_id = str(package.id)
        
        if not offering_id:
            return jsonify({'error': 'Offering not found'}), 404
        
        # Collect customers who purchased this offering
        customer_purchases = {}
        
        for bill in bills:
            if not bill.customer:
                continue
                
            customer_id = str(bill.customer.id)
            customer_name = f"{bill.customer.first_name or ''} {bill.customer.last_name or ''}".strip()
            
            for item in (bill.items or []):
                try:
                    item_type = getattr(item, 'item_type', None)
                    if item_type != offering_type:
                        continue
                    
                    item_offering_id = None
                    if item_type == 'service' and hasattr(item, 'service') and item.service:
                        item_offering_id = str(item.service.id) if hasattr(item.service, 'id') else None
                    elif item_type == 'product' and hasattr(item, 'product') and item.product:
                        item_offering_id = str(item.product.id) if hasattr(item.product, 'id') else None
                    elif item_type == 'package' and hasattr(item, 'package') and item.package:
                        item_offering_id = str(item.package.id) if hasattr(item.package, 'id') else None
                    
                    if item_offering_id == offering_id:
                        if customer_id not in customer_purchases:
                            customer_purchases[customer_id] = {
                                'customer_id': customer_id,
                                'customer_name': customer_name or 'Unknown',
                                'mobile': bill.customer.mobile or '-',
                                'email': bill.customer.email or '-',
                                'purchase_count': 0,
                                'total_spent': 0.0,
                                'last_purchase_date': None
                            }
                        
                        customer_purchases[customer_id]['purchase_count'] += _safe_int(item.quantity, default=1)
                        customer_purchases[customer_id]['total_spent'] += _safe_float(item.total)
                        
                        # Update last purchase date
                        bill_date = bill.bill_date
                        if bill_date:
                            if not customer_purchases[customer_id]['last_purchase_date'] or bill_date > customer_purchases[customer_id]['last_purchase_date']:
                                customer_purchases[customer_id]['last_purchase_date'] = bill_date
                except (AttributeError, TypeError, ValueError) as e:
                    continue
        
        # Convert to list and sort by total spent
        clients = sorted(
            customer_purchases.values(),
            key=lambda x: x['total_spent'],
            reverse=True
        )
        
        # Format dates
        for client in clients:
            if client['last_purchase_date']:
                if isinstance(client['last_purchase_date'], datetime):
                    client['last_purchase_date'] = client['last_purchase_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'offering': {
                'name': offering_name,
                'type': offering_type
            },
            'clients': clients,
            'total_clients': len(clients)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/revenue-breakdown', methods=['GET'])
@require_auth
def get_revenue_breakdown(current_user=None):
    """Get revenue breakdown by source"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)

        breakdown = {
            'service': 0,
            'product': 0,
            'package': 0,
            'prepaid': 0,
            'membership': 0
        }

        for bill in bills:
            for item in bill.items:
                if item.item_type in breakdown:
                    breakdown[item.item_type] += float(item.total) if item.total else 0.0

        total = sum(breakdown.values())

        return jsonify({
            'breakdown': {
                key: {
                    'amount': round(value, 2),
                    'percentage': round((value / total * 100) if total > 0 else 0, 2)
                }
                for key, value in breakdown.items()
            },
            'total': round(total, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/payment-distribution', methods=['GET'])
@require_auth
def get_payment_distribution(current_user=None):
    """Get payment method breakdown"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end,
            payment_mode__ne=None
        )
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)
        
        # Group by payment mode
        payment_stats = {}
        for bill in bills:
            mode = bill.payment_mode or 'unknown'
            if mode not in payment_stats:
                payment_stats[mode] = {'total_amount': 0.0, 'count': 0}
            payment_stats[mode]['total_amount'] += float(bill.final_amount) if bill.final_amount else 0.0
            payment_stats[mode]['count'] += 1
        
        total = sum([stats['total_amount'] for stats in payment_stats.values()])

        return jsonify({
            'distribution': [{
                'payment_mode': mode,
                'amount': round(stats['total_amount'], 2),
                'count': stats['count'],
                'percentage': round((stats['total_amount'] / total * 100) if total > 0 else 0, 2)
            } for mode, stats in payment_stats.items()],
            'total': round(total, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-moving-items', methods=['GET'])
@require_auth
def get_top_moving_items(current_user=None):
    """Get top moving items (services, packages, products) with trends and stock status"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
        else:
            # Default to last 30 days (using IST)
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            default_end_date = today_ist
            start, end = get_ist_date_range(default_start_date, default_end_date)
        
        # Get bills in current period
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        current_bills = list(bills_query)
        
        # Calculate previous period for trend comparison
        if start_date and end_date:
            # Calculate period length
            period_start = datetime.strptime(start_date, '%Y-%m-%d')
            period_end = datetime.strptime(end_date, '%Y-%m-%d')
            period_days = (period_end - period_start).days + 1
            prev_start_date = (period_start - timedelta(days=period_days)).strftime('%Y-%m-%d')
            prev_end_date = (period_start - timedelta(days=1)).strftime('%Y-%m-%d')
            prev_start, prev_end = get_ist_date_range(prev_start_date, prev_end_date)
        else:
            # Default: compare with previous 30 days (using IST)
            today_ist = get_ist_today()
            prev_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=60)
            prev_start_date = prev_start_date_obj.strftime('%Y-%m-%d')
            prev_end_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=31)
            prev_end_date = prev_end_date_obj.strftime('%Y-%m-%d')
            prev_start, prev_end = get_ist_date_range(prev_start_date, prev_end_date)
        
        # Get bills in previous period
        prev_bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=prev_start,
            bill_date__lte=prev_end
        )
        if branch:
            prev_bills_query = prev_bills_query.filter(branch=branch)
        prev_bills = list(prev_bills_query)
        
        # Services: Name, Bills count, Revenue, Trend
        services_stats = {}
        services_prev_stats = {}
        
        for bill in current_bills:
            for item in (bill.items or []):
                try:
                    if getattr(item, 'item_type', None) == 'service' and item.service:
                        item.service.reload()
                        service_id = str(item.service.id)
                        service_name = item.service.name if hasattr(item.service, 'name') else 'Service'
                        if service_id not in services_stats:
                            services_stats[service_id] = {
                                'name': service_name,
                                'bills': set(),
                                'revenue': 0.0
                            }
                        services_stats[service_id]['bills'].add(str(bill.id))
                        services_stats[service_id]['revenue'] += _safe_float(item.total)
                except (DoesNotExist, AttributeError, TypeError, ValueError):
                    continue
        
        for bill in prev_bills:
            for item in (bill.items or []):
                try:
                    if getattr(item, 'item_type', None) == 'service' and item.service:
                        item.service.reload()
                        service_id = str(item.service.id)
                        if service_id not in services_prev_stats:
                            services_prev_stats[service_id] = {'revenue': 0.0}
                        services_prev_stats[service_id]['revenue'] += _safe_float(item.total)
                except (DoesNotExist, AttributeError, TypeError, ValueError):
                    continue
        
        # Calculate trends for services
        services_list = []
        for service_id, stats in services_stats.items():
            current_revenue = stats['revenue']
            prev_revenue = services_prev_stats.get(service_id, {}).get('revenue', 0.0)
            
            if prev_revenue == 0:
                trend = 'trending_up' if current_revenue > 0 else 'minus'
            elif current_revenue > prev_revenue * 1.1:  # 10% increase
                trend = 'trending_up'
            elif current_revenue < prev_revenue * 0.9:  # 10% decrease
                trend = 'trending_down'
            else:
                trend = 'minus'
            
            services_list.append({
                'name': stats['name'],
                'bills': len(stats['bills']),
                'revenue': round(current_revenue, 2),
                'trend': trend
            })
        
        # Sort by revenue and limit to top 10
        services_list = sorted(services_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        # Packages: Name, Sold count, Revenue, Status
        packages_stats = {}
        
        for bill in current_bills:
            for item in (bill.items or []):
                try:
                    if getattr(item, 'item_type', None) == 'package' and item.package:
                        item.package.reload()
                        package_id = str(item.package.id)
                        package_name = item.package.name if hasattr(item.package, 'name') else 'Package'
                        if package_id not in packages_stats:
                            packages_stats[package_id] = {
                                'name': package_name,
                                'sold': 0,
                                'revenue': 0.0
                            }
                        packages_stats[package_id]['sold'] += _safe_int(item.quantity, default=1)
                        packages_stats[package_id]['revenue'] += _safe_float(item.total)
                except (DoesNotExist, AttributeError, TypeError, ValueError):
                    continue
        
        # Calculate average sales per package for status
        if packages_stats:
            avg_sales = sum(p['sold'] for p in packages_stats.values()) / len(packages_stats)
        else:
            avg_sales = 0
        
        packages_list = []
        for package_id, stats in packages_stats.items():
            if stats['sold'] > avg_sales * 1.2:
                status = 'High Demand'
            elif stats['sold'] < avg_sales * 0.8:
                status = 'Low Demand'
            else:
                status = 'Stable'
            
            packages_list.append({
                'name': stats['name'],
                'sold': stats['sold'],
                'revenue': round(stats['revenue'], 2),
                'status': status
            })
        
        # Sort by revenue and limit to top 10
        packages_list = sorted(packages_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        # Products: Name, Sold count, Revenue, Stock status
        products_stats = {}
        
        for bill in current_bills:
            for item in (bill.items or []):
                try:
                    if getattr(item, 'item_type', None) == 'product' and item.product:
                        item.product.reload()
                        product_id = str(item.product.id)
                        product_name = item.product.name if hasattr(item.product, 'name') else 'Product'
                        if product_id not in products_stats:
                            products_stats[product_id] = {
                                'name': product_name,
                                'sold': 0,
                                'revenue': 0.0,
                                'stock_quantity': item.product.stock_quantity if item.product.stock_quantity is not None else 0,
                                'min_stock_level': item.product.min_stock_level if hasattr(item.product, 'min_stock_level') else 0
                            }
                        products_stats[product_id]['sold'] += _safe_int(item.quantity, default=1)
                        products_stats[product_id]['revenue'] += _safe_float(item.total)
                except (DoesNotExist, AttributeError, TypeError, ValueError):
                    continue
        
        products_list = []
        for product_id, stats in products_stats.items():
            stock_status = 'OK'
            if stats['stock_quantity'] is not None and stats['min_stock_level'] is not None:
                if stats['stock_quantity'] <= stats['min_stock_level']:
                    stock_status = 'Low'
            
            products_list.append({
                'name': stats['name'],
                'sold': stats['sold'],
                'revenue': round(stats['revenue'], 2),
                'stock': stock_status
            })
        
        # Sort by revenue and limit to top 10
        products_list = sorted(products_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        return jsonify({
            'services': services_list,
            'packages': packages_list,
            'products': products_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/client-funnel', methods=['GET'])
@require_auth
def get_client_funnel(current_user=None):
    """Get client acquisition funnel"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert IST dates to UTC for filtering
        if start_date:
            start = ist_to_utc_start(start_date)
        else:
            # Default to 30 days ago in IST, convert to UTC
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            start = ist_to_utc_start(default_start_date)

        if end_date:
            end = ist_to_utc_end(end_date)
        else:
            # Default to today in IST, convert to UTC
            end = ist_to_utc_end(get_ist_today())

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)

        # Total customers - filter by branch
        customers_query = Customer.objects
        if branch:
            customers_query = customers_query.filter(branch=branch)
        total_customers = customers_query.count()

        # New customers in period - filter by branch
        new_customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            new_customers_query = new_customers_query.filter(branch=branch)
        new_customers = new_customers_query.count()

        # Returning customers (with more than 1 bill) - filter by branch
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills_in_period = list(bills_query)
        customer_bill_count = {}
        for bill in bills_in_period:
            if bill.customer:
                customer_id = str(bill.customer.id)
                customer_bill_count[customer_id] = customer_bill_count.get(customer_id, 0) + 1
        returning_customers = len([cid for cid, count in customer_bill_count.items() if count > 1])

        # Leads
        total_leads = Lead.objects.count()
        converted_leads = Lead.objects(converted_to_customer=True).count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        return jsonify({
            'customers': {
                'total': total_customers,
                'new': new_customers,
                'returning': returning_customers
            },
            'leads': {
                'total': total_leads,
                'converted': converted_leads,
                'conversion_rate': round(conversion_rate, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/client-source', methods=['GET'])
@require_auth
def get_client_source(current_user=None):
    """Get client source distribution"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert IST dates to UTC for filtering
        if start_date:
            start = ist_to_utc_start(start_date)
        else:
            # Default to 30 days ago in IST, convert to UTC
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            start = ist_to_utc_start(default_start_date)

        if end_date:
            end = ist_to_utc_end(end_date)
        else:
            # Default to today in IST, convert to UTC
            end = ist_to_utc_end(get_ist_today())

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)

        # Get customers in date range - filter by branch
        customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            customers_query = customers_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        customers = list(customers_query)
        
        # Group by source
        source_stats = {}
        for customer in customers:
            source = customer.source or 'Unknown'
            if source not in source_stats:
                source_stats[source] = {
                    'count': 0,
                    'revenue': 0.0
                }
            source_stats[source]['count'] += 1
        
        # Calculate revenue per source from bills
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        bills = list(bills_query)
        for bill in bills:
            if bill.customer and bill.customer.source:
                source = bill.customer.source
                if source in source_stats:
                    source_stats[source]['revenue'] += float(bill.final_amount) if bill.final_amount else 0.0
        
        # Convert to list format
        distribution = []
        total_customers = sum(s['count'] for s in source_stats.values())
        total_revenue = sum(s['revenue'] for s in source_stats.values())
        
        for source, stats in source_stats.items():
            distribution.append({
                'source': source,
                'count': stats['count'],
                'revenue': round(stats['revenue'], 2),
                'percentage': round((stats['count'] / total_customers * 100) if total_customers > 0 else 0, 2)
            })
        
        # Sort by count descending
        distribution.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'distribution': distribution,
            'total_customers': total_customers,
            'total_revenue': round(total_revenue, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
@require_auth
def get_operational_alerts(current_user=None):
    """Get operational alerts"""
    try:
        alerts = []

        # Low stock products - compare stock_quantity with min_stock_level for each product
        low_stock_products = 0
        try:
            all_products = Product.objects(status='active')
            for product in all_products:
                if product.stock_quantity is not None and product.min_stock_level is not None:
                    if product.stock_quantity <= product.min_stock_level:
                        low_stock_products += 1
        except Exception:
            low_stock_products = 0

        if low_stock_products > 0:
            alerts.append({
                'type': 'low_stock',
                'severity': 'warning',
                'message': f'{low_stock_products} product(s) are running low on stock',
                'count': low_stock_products
            })

        # Cancelled bills today (using IST)
        today_ist_str = get_ist_today()
        today_start, today_end = get_ist_date_range(today_ist_str, today_ist_str)
        cancelled_bills = Bill.objects(
            is_deleted=True,
            deleted_at__gte=today_start,
            deleted_at__lte=today_end
        ).count()

        if cancelled_bills > 0:
            alerts.append({
                'type': 'cancelled_bills',
                'severity': 'info',
                'message': f'{cancelled_bills} bill(s) cancelled today',
                'count': cancelled_bills
            })

        # No-show appointments today (using IST)
        today_ist_date = datetime.strptime(today_ist_str, '%Y-%m-%d').date()
        no_shows = Appointment.objects(
            appointment_date=today_ist_date,
            status='no-show'
        ).count()

        if no_shows > 0:
            alerts.append({
                'type': 'no_shows',
                'severity': 'warning',
                'message': f'{no_shows} no-show appointment(s) today',
                'count': no_shows
            })

        # Upcoming appointments today (using IST)
        upcoming = Appointment.objects(
            appointment_date=today_ist_date,
            status='confirmed'
        ).count()

        if upcoming > 0:
            alerts.append({
                'type': 'upcoming_appointments',
                'severity': 'info',
                'message': f'{upcoming} upcoming appointment(s) today',
                'count': upcoming
            })

        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-performer', methods=['GET'])
@require_auth
def get_top_performer(current_user=None):
    """Calculate top performer based on weighted scoring system (company-wide)"""
    
    def safe_get_staff_id(item_staff):
        """Safely get staff ID from a staff reference, handling DBRef and broken references"""
        if not item_staff:
            return None
        try:
            # Try to access as dereferenced object
            if hasattr(item_staff, 'id'):
                try:
                    return str(item_staff.id)
                except (AttributeError, DoesNotExist):
                    # Staff document might be deleted, try to get ID from DBRef
                    if hasattr(item_staff, 'pk'):
                        return str(item_staff.pk)
                    return None
            # If it's already a string
            elif isinstance(item_staff, str):
                return item_staff
            # If it's an ObjectId (from bson)
            elif hasattr(item_staff, '__str__'):
                try:
                    return str(item_staff)
                except:
                    return None
        except (AttributeError, DoesNotExist, TypeError, ValueError) as e:
            # Silently handle errors - broken references are common
            return None
        return None
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Default to last 30 days if no date range provided (using IST)
        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get branch for filtering (used only for feedback)
        branch = get_selected_branch(request, current_user)
        
        # Get ALL active staff (company-wide, not filtered by branch)
        staff_list = list(Staff.objects(status='active'))
        
        # Get ALL bills in date range (company-wide, not filtered by branch)
        # Convert to list to avoid multiple query iterations
        bills = list(Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        ))
        
        # Calculate max values for normalization
        max_revenue = 0
        max_services = 0
        max_appts = 0
        
        # First pass: calculate max values
        for staff in staff_list:
            try:
                staff_id = str(staff.id)

                # Calculate revenue
                revenue = 0
                service_count = 0
                for bill in bills:
                    for item in (bill.items or []):
                        try:
                            item_staff_id = safe_get_staff_id(item.staff)
                            if item_staff_id and item_staff_id == staff_id:
                                revenue += float(item.total) if item.total else 0.0
                                service_count += int(item.quantity) if item.quantity else 1
                        except (AttributeError, TypeError, ValueError, DoesNotExist):
                            # Skip items with invalid staff references or data
                            continue

                # Calculate appointments
                try:
                    appointments = Appointment.objects(
                        staff=staff,
                        appointment_date__gte=start.date(),
                        appointment_date__lte=end.date(),
                        status='completed'
                    ).count()
                except Exception:
                    appointments = 0

                max_revenue = max(max_revenue, revenue)
                max_services = max(max_services, service_count)
                max_appts = max(max_appts, appointments)
            except Exception as staff_error:
                print(f"Warning: Failed to compute max values for staff {getattr(staff, 'id', 'unknown')}: {staff_error}")
                continue
        
        # Avoid division by zero
        max_revenue = max_revenue if max_revenue > 0 else 1
        max_services = max_services if max_services > 0 else 1
        max_appts = max_appts if max_appts > 0 else 1
        
        scores = []
        
        # Second pass: calculate scores
        for staff in staff_list:
            try:
                staff_id = str(staff.id)

                # 1. Revenue (40%)
                revenue = 0
                service_count = 0
                for bill in bills:
                    for item in (bill.items or []):
                        try:
                            item_staff_id = safe_get_staff_id(item.staff)
                            if item_staff_id and item_staff_id == staff_id:
                                revenue += float(item.total) if item.total else 0.0
                                service_count += int(item.quantity) if item.quantity else 1
                        except (AttributeError, TypeError, ValueError, DoesNotExist):
                            # Skip items with invalid staff references or data
                            continue

                revenue_score = (revenue / max_revenue) * 40

                # 2. Service Count (20%)
                service_score = (service_count / max_services) * 20

                # 3. Appointments (15%)
                try:
                    appointments = Appointment.objects(
                        staff=staff,
                        appointment_date__gte=start.date(),
                        appointment_date__lte=end.date(),
                        status='completed'
                    ).count()
                except Exception:
                    appointments = 0
                appt_score = (appointments / max_appts) * 15

                # 4. Feedback Rating (15%)
                try:
                    feedbacks = list(Feedback.objects(
                        staff=staff,
                        created_at__gte=start,
                        created_at__lte=end
                    ))
                except Exception:
                    feedbacks = []

                feedback_count = len(feedbacks)
                if feedback_count > 0:
                    try:
                        total_rating = sum(float(f.rating) for f in feedbacks if f.rating is not None)
                        avg_rating = total_rating / feedback_count if feedback_count > 0 else 0.0
                        rating_score = (avg_rating / 5.0) * 15 if avg_rating > 0 else 0.0
                    except (TypeError, ValueError, ZeroDivisionError):
                        avg_rating = 0.0
                        rating_score = 0.0
                else:
                    avg_rating = 0.0
                    rating_score = 0.0

                # 5. Customer Retention (10%)
                # Count repeat customers who requested this staff
                customer_visits = {}
                for bill in bills:
                    try:
                        if bill.customer and hasattr(bill.customer, 'id'):
                            customer_id = str(bill.customer.id)
                            # Check if this bill has items from this staff
                            has_staff_item = False
                            for item in (bill.items or []):
                                try:
                                    item_staff_id = safe_get_staff_id(item.staff)
                                    if item_staff_id and item_staff_id == staff_id:
                                        has_staff_item = True
                                        break
                                except (AttributeError, TypeError, DoesNotExist):
                                    continue

                            if has_staff_item:
                                if customer_id not in customer_visits:
                                    customer_visits[customer_id] = 0
                                customer_visits[customer_id] += 1
                    except (AttributeError, TypeError, DoesNotExist):
                        # Skip bills with invalid customer references
                        continue

                # Calculate retention rate (customers with 2+ visits)
                total_customers = len(customer_visits)
                repeat_customers = sum(1 for visits in customer_visits.values() if visits >= 2)
                retention_rate = (repeat_customers / total_customers) if total_customers > 0 else 0
                retention_score = retention_rate * 10

                # Calculate total performance score
                total_score = revenue_score + service_score + appt_score + rating_score + retention_score

                scores.append({
                    'staff_id': staff_id,
                    'staff_name': f"{staff.first_name or ''} {staff.last_name or ''}".strip(),
                    'performance_score': round(float(total_score), 1),
                    'revenue': round(float(revenue), 2),
                    'service_count': int(service_count),
                    'completed_appointments': int(appointments),
                    'avg_rating': round(float(avg_rating), 2),
                    'feedback_count': int(feedback_count),
                    'retention_rate': round(float(retention_rate) * 100, 1)
                })
            except Exception as staff_error:
                print(f"Warning: Failed to compute score for staff {getattr(staff, 'id', 'unknown')}: {staff_error}")
                continue
        
        # Sort by performance score
        scores.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return jsonify({
            'top_performer': scores[0] if scores else None,
            'leaderboard': scores
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_top_performer: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500
