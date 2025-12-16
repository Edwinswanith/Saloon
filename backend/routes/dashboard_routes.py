from flask import Blueprint, request, jsonify
from models import Bill, Customer, Staff, Expense, Product, Appointment, Lead
from datetime import datetime, timedelta, date
from mongoengine import Q

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        # Total revenue from bills
        bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        total_revenue = sum([float(b.final_amount) for b in bills]) if bills else 0.0

        # Total transactions (bills)
        total_transactions = bills.count()

        # Total expenses
        expenses = Expense.objects(
            expense_date__gte=start.date(),
            expense_date__lte=end.date()
        )
        total_expenses = sum([float(e.amount) for e in expenses]) if expenses else 0.0

        # Net profit
        net_profit = float(total_revenue) - float(total_expenses)

        # Average bill value
        avg_bill_value = float(total_revenue) / int(total_transactions) if total_transactions > 0 else 0.0

        # Total customers
        total_customers = Customer.objects.count()

        # New customers in period
        new_customers = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        ).count()

        # Total staff
        active_staff = Staff.objects(status='active').count()

        # Appointments stats
        total_appointments = Appointment.objects(
            appointment_date__gte=start.date(),
            appointment_date__lte=end.date()
        ).count()

        completed_appointments = Appointment.objects(
            appointment_date__gte=start.date(),
            appointment_date__lte=end.date(),
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
def get_staff_performance():
    """Get staff performance metrics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        # Get all active staff
        staff_list = Staff.objects(status='active')

        performance = []
        for staff in staff_list:
            # Get bills with items served by this staff
            bills = Bill.objects(
                is_deleted=False,
                bill_date__gte=start,
                bill_date__lte=end
            )
            
            total_revenue = 0.0
            total_services = 0
            for bill in bills:
                for item in bill.items:
                    if item.staff and str(item.staff.id) == str(staff.id):
                        total_revenue += float(item.total) if item.total else 0.0
                        total_services += 1

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
                'commission_earned': round(commission, 2),
                'completed_appointments': completed_appointments
            })

        # Sort by revenue
        performance.sort(key=lambda x: x['total_revenue'], reverse=True)

        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-customers', methods=['GET'])
def get_top_customers():
    """Get top 10 customers by revenue"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        # Get bills in date range
        bills_query = Bill.objects(is_deleted=False)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            bills_query = bills_query.filter(bill_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            bills_query = bills_query.filter(bill_date__lte=end)
        
        bills = bills_query
        
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
def get_top_offerings():
    """Get top 10 services/products by revenue"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        bills_query = Bill.objects(is_deleted=False)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            bills_query = bills_query.filter(bill_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            bills_query = bills_query.filter(bill_date__lte=end)
        
        bills = bills_query

        # Group by service/product/package
        offerings = {}
        for bill in bills:
            for item in bill.items:
                key = None
                name = None

                if item.item_type == 'service' and item.service:
                    key = f"service_{str(item.service.id)}"
                    name = item.service.name
                elif item.item_type == 'product' and item.product:
                    key = f"product_{str(item.product.id)}"
                    name = item.product.name
                elif item.item_type == 'package' and item.package:
                    key = f"package_{str(item.package.id)}"
                    name = item.package.name

                if key and name:
                    if key not in offerings:
                        offerings[key] = {
                            'name': name,
                            'type': item.item_type,
                            'revenue': 0,
                            'quantity': 0
                        }

                    offerings[key]['revenue'] += float(item.total) if item.total else 0.0
                    offerings[key]['quantity'] += int(item.quantity) if item.quantity else 0

        # Convert to list and sort
        top_offerings = sorted(offerings.values(), key=lambda x: x['revenue'], reverse=True)[:limit]

        return jsonify([{
            'name': o['name'],
            'type': o['type'],
            'revenue': round(o['revenue'], 2),
            'quantity': o['quantity']
        } for o in top_offerings])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/revenue-breakdown', methods=['GET'])
def get_revenue_breakdown():
    """Get revenue breakdown by source"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )

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
def get_payment_distribution():
    """Get payment method breakdown"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end,
            payment_mode__ne=None
        )
        
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

@dashboard_bp.route('/client-funnel', methods=['GET'])
def get_client_funnel():
    """Get client acquisition funnel"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = datetime.now()

        # Total customers
        total_customers = Customer.objects.count()

        # New customers in period
        new_customers = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        ).count()

        # Returning customers (with more than 1 bill)
        bills_in_period = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
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

@dashboard_bp.route('/alerts', methods=['GET'])
def get_operational_alerts():
    """Get operational alerts"""
    try:
        alerts = []

        # Low stock products
        low_stock_products = Product.objects(
            stock_quantity__lte=Product.min_stock_level,
            status='active'
        ).count()

        if low_stock_products > 0:
            alerts.append({
                'type': 'low_stock',
                'severity': 'warning',
                'message': f'{low_stock_products} product(s) are running low on stock',
                'count': low_stock_products
            })

        # Cancelled bills today
        today = datetime.now().date()
        cancelled_bills = Bill.objects(
            is_deleted=True,
            deleted_at__gte=datetime.combine(today, datetime.min.time()),
            deleted_at__lt=datetime.combine(today, datetime.max.time())
        ).count()

        if cancelled_bills > 0:
            alerts.append({
                'type': 'cancelled_bills',
                'severity': 'info',
                'message': f'{cancelled_bills} bill(s) cancelled today',
                'count': cancelled_bills
            })

        # No-show appointments today
        no_shows = Appointment.objects(
            appointment_date=today,
            status='no-show'
        ).count()

        if no_shows > 0:
            alerts.append({
                'type': 'no_shows',
                'severity': 'warning',
                'message': f'{no_shows} no-show appointment(s) today',
                'count': no_shows
            })

        # Upcoming appointments today
        upcoming = Appointment.objects(
            appointment_date=today,
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
