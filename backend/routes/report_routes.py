from flask import Blueprint, request, jsonify
from models import Bill, Branch, Service, ServiceGroup, Staff, Customer, Expense, Product, Membership, Appointment
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import (
    apply_branch_scope,
    apply_branch_scope_to_match,
    get_demo_branch_exclusion,
    get_selected_branch,
)
from utils.date_utils import get_ist_date_range, get_ist_today
from utils.staff_revenue import attributed_revenue_pipeline

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
        bills_query = apply_branch_scope(bills_query, branch, current_user)

        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)

        bills = list(bills_query.no_dereference().only('items'))

        def _ref_id(doc, field):
            raw = doc._data.get(field) if hasattr(doc, '_data') else None
            if raw is None:
                return None
            return raw.id if hasattr(raw, 'id') else raw

        service_ids = set()
        for bill in bills:
            for item in bill.items:
                if item.item_type == 'service':
                    sid = _ref_id(item, 'service')
                    if sid is not None:
                        service_ids.add(sid)

        service_map = {}
        if service_ids:
            for s in Service.objects(id__in=list(service_ids)).no_dereference().only('name', 'group'):
                service_map[s.id] = s

        group_ids = {_ref_id(s, 'group') for s in service_map.values()}
        group_ids.discard(None)
        group_name_map = {}
        if group_ids:
            for g in ServiceGroup.objects(id__in=list(group_ids)).only('name'):
                group_name_map[g.id] = g.name

        service_stats = {}
        for bill in bills:
            for item in bill.items:
                if item.item_type != 'service':
                    continue
                sid = _ref_id(item, 'service')
                svc = service_map.get(sid) if sid is not None else None
                if not svc:
                    continue

                gid = _ref_id(svc, 'group')
                service_group_name = group_name_map.get(gid) if gid is not None else None

                if service_group and service_group != 'all':
                    if not service_group_name or service_group_name.lower() != service_group.lower():
                        continue

                key = str(sid)
                if key not in service_stats:
                    service_stats[key] = {
                        'service_name': svc.name or 'Unknown Service',
                        'service_group': service_group_name,
                        'count': 0,
                        'revenue': 0
                    }
                service_stats[key]['count'] += int(item.quantity) if item.quantity else 0
                service_stats[key]['revenue'] += float(item.total) if item.total else 0.0

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
        query = apply_branch_scope(query, branch, current_user)

        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                query = query.filter(bill_date__gte=start)
            if end:
                query = query.filter(bill_date__lte=end)
        if customer_id and ObjectId.is_valid(customer_id):
            query = query.filter(customer=ObjectId(customer_id))

        # Only load the fields this endpoint actually needs, and skip auto-
        # dereferencing the customer ref. We batch-fetch customers below in one
        # query, avoiding the N+1 round-trips to Atlas that made this endpoint
        # take up to 2 minutes.
        bills = list(
            query.order_by('-bill_date')
                 .no_dereference()
                 .only(
                     'bill_number', 'bill_date', 'customer',
                     'subtotal', 'discount_amount', 'tax_amount',
                     'final_amount', 'payment_mode', 'booking_status'
                 )
        )

        customer_ids = set()
        for b in bills:
            cref = b._data.get('customer')
            if cref is None:
                continue
            cid = getattr(cref, 'id', cref)
            if cid is not None:
                customer_ids.add(cid)

        customer_map = {}
        if customer_ids:
            for c in Customer.objects(id__in=list(customer_ids)).only(
                'first_name', 'last_name', 'mobile'
            ):
                customer_map[c.id] = c

        result = []
        for b in bills:
            try:
                bill_date_iso = b.bill_date.isoformat() if b.bill_date else None

                cref = b._data.get('customer')
                cid = getattr(cref, 'id', cref) if cref is not None else None
                customer = customer_map.get(cid)
                if customer is not None:
                    name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'Walk-in'
                    mobile = customer.mobile
                    cust_id_str = str(customer.id)
                else:
                    name = 'Walk-in'
                    mobile = None
                    cust_id_str = None

                result.append({
                    'bill_number': b.bill_number,
                    'bill_date': bill_date_iso,
                    'customer_name': name,
                    'customer_mobile': mobile,
                    'customer_id': cust_id_str,
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
        query = apply_branch_scope(query, branch, current_user)

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
        bills_query = apply_branch_scope(bills_query, branch, current_user)

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

@report_bp.route('/membership-clients', methods=['GET'])
@require_role('manager', 'owner')
def membership_clients_report(current_user=None):
    """Active membership clients (Manager and Owner only)"""
    try:
        status = request.args.get('status', 'active')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        memberships_query = Membership.objects(status=status)
        # When listing 'active' members, only those whose expiry_date is in the
        # future actually count — otherwise expired-but-not-yet-flipped records
        # leak in. Other status filters (expired/replaced) keep no expiry filter.
        if status == 'active':
            memberships_query = memberships_query.filter(expiry_date__gte=datetime.utcnow())
        memberships_query = apply_branch_scope(memberships_query, branch, current_user)
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
        start, end = get_ist_date_range(start_date, end_date)
        period_days = 30
        if start_date and end_date:
            start_day = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_day = datetime.strptime(end_date, '%Y-%m-%d').date()
            period_days = max((end_day - start_day).days + 1, 1)

        staff_query = Staff.objects(status='active')
        staff_query = apply_branch_scope(staff_query, branch, current_user)
        staff_map = {str(staff.id): staff for staff in staff_query}

        bills_query = Bill.objects(is_deleted=False)
        bills_query = apply_branch_scope(bills_query, branch, current_user)
        if start:
            bills_query = bills_query.filter(bill_date__gte=start)
        if end:
            bills_query = bills_query.filter(bill_date__lte=end)

        performance = {}

        def ensure_staff_row(staff):
            staff_id = str(staff.id)
            if staff_id not in performance:
                performance[staff_id] = {
                    'staff': staff,
                    'service_revenue': 0.0,
                    'package_revenue': 0.0,
                    'product_revenue': 0.0,
                    'membership_revenue': 0.0,
                    'total_revenue': 0.0,
                    'item_count': 0,
                    'bill_ids': set(),
                }
            return performance[staff_id]

        for staff in staff_map.values():
            ensure_staff_row(staff)

        for bill in bills_query:
            bill_id = str(bill.id)
            for item in bill.items or []:
                if not item.staff:
                    continue
                staff_id = str(item.staff.id)
                if staff_id not in staff_map:
                    staff_map[staff_id] = item.staff
                row = ensure_staff_row(staff_map[staff_id])
                item_total = float(item.total or 0)
                quantity = int(item.quantity or 1)

                row['total_revenue'] += item_total
                row['item_count'] += quantity
                row['bill_ids'].add(bill_id)

                if item.item_type == 'service':
                    row['service_revenue'] += item_total
                elif item.item_type == 'package':
                    row['package_revenue'] += item_total
                elif item.item_type == 'product':
                    row['product_revenue'] += item_total
                elif item.item_type == 'membership':
                    row['membership_revenue'] += item_total

        report = []
        for row in performance.values():
            staff = row['staff']
            total_revenue = row['total_revenue']
            bill_count = len(row['bill_ids'])
            avg_bill = total_revenue / bill_count if bill_count > 0 else 0
            commission_rate = float(staff.commission_rate or 0)
            commission = total_revenue * (commission_rate / 100)

            incentive_threshold = float(getattr(staff, 'incentive_threshold', 50000.0) or 50000.0)
            incentive_rate = float(getattr(staff, 'incentive_rate', 0.0) or 0.0)
            incentive_base = max(total_revenue - incentive_threshold, 0.0) if incentive_rate > 0 else 0.0
            incentive_eligible = incentive_base > 0
            incentive_amount = incentive_base * (incentive_rate / 100)
            revenue_to_target = max(incentive_threshold - total_revenue, 0.0) if incentive_rate > 0 else 0.0
            target_progress = (total_revenue / incentive_threshold * 100) if incentive_threshold > 0 else 0
            monthly_salary = float(staff.salary or 0)
            period_salary = monthly_salary * (period_days / 30.0)
            variable_pay = commission + incentive_amount
            total_earnings = period_salary + variable_pay

            if incentive_rate <= 0:
                incentive_status = 'not_configured'
            elif incentive_eligible:
                incentive_status = 'earned'
            else:
                incentive_status = 'target_not_met'

            report.append({
                'staff_id': str(staff.id),
                'staff_name': f"{staff.first_name or ''} {staff.last_name or ''}".strip() or 'Staff',
                'staff_status': staff.status,
                'bill_count': bill_count,
                'item_count': row['item_count'],
                'service': round(row['service_revenue'], 2),
                'package': round(row['package_revenue'], 2),
                'product': round(row['product_revenue'], 2),
                'membership': round(row['membership_revenue'], 2),
                'total': round(total_revenue, 2),
                'avg_bill': round(avg_bill, 2),
                'total_revenue': round(total_revenue, 2),
                'commission_rate': round(commission_rate, 2),
                'commission_earned': round(commission, 2),
                'salary': round(monthly_salary, 2),
                'period_salary': round(period_salary, 2),
                'period_days': period_days,
                'incentive_threshold': round(incentive_threshold, 2),
                'incentive_rate': round(incentive_rate, 2),
                'incentive_base': round(incentive_base, 2),
                'incentive_eligible': incentive_eligible,
                'incentive_status': incentive_status,
                'incentive_amount': round(incentive_amount, 2),
                'revenue_to_target': round(revenue_to_target, 2),
                'target_progress_percent': round(target_progress, 2),
                'variable_pay': round(variable_pay, 2),
                'total_earnings': round(total_earnings, 2),
                'calculation_note': (
                    f"Commission: revenue x {round(commission_rate, 2)}%. "
                    f"Incentive: max(revenue - target, 0) x {round(incentive_rate, 2)}%."
                )
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


@report_bp.route('/my-incentive', methods=['GET'])
@require_auth
def my_incentive_report(current_user=None):
    """Self-only incentive progress for the logged-in staff user."""
    try:
        if not current_user or current_user.get('user_type') != 'staff':
            return jsonify({'error': 'This endpoint is available for staff login only'}), 403

        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id or not ObjectId.is_valid(user_id):
            return jsonify({'error': 'Invalid staff user'}), 400

        staff = Staff.objects(id=user_id).first()
        if not staff:
            return jsonify({'error': 'Staff member not found'}), 404

        today = datetime.strptime(get_ist_today(), '%Y-%m-%d').date()
        start_date = request.args.get('start_date') or today.replace(day=1).strftime('%Y-%m-%d')
        end_date = request.args.get('end_date') or today.strftime('%Y-%m-%d')
        start, end = get_ist_date_range(start_date, end_date)

        start_day = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_day = datetime.strptime(end_date, '%Y-%m-%d').date()
        period_days = max((end_day - start_day).days + 1, 1)

        branch = get_selected_branch(request, current_user)
        bills_query = Bill.objects(is_deleted=False, bill_date__gte=start, bill_date__lte=end)
        bills_query = apply_branch_scope(bills_query, branch, current_user)

        staff_id = str(staff.id)
        service_revenue = 0.0
        package_revenue = 0.0
        product_revenue = 0.0
        membership_revenue = 0.0
        total_revenue = 0.0
        item_count = 0
        bill_ids = set()

        for bill in bills_query:
            bill_has_staff_item = False
            for item in bill.items or []:
                if not item.staff or str(item.staff.id) != staff_id:
                    continue

                bill_has_staff_item = True
                item_total = float(item.total or 0)
                quantity = int(item.quantity or 1)
                total_revenue += item_total
                item_count += quantity

                if item.item_type == 'service':
                    service_revenue += item_total
                elif item.item_type == 'package':
                    package_revenue += item_total
                elif item.item_type == 'product':
                    product_revenue += item_total
                elif item.item_type == 'membership':
                    membership_revenue += item_total

            if bill_has_staff_item:
                bill_ids.add(str(bill.id))

        bill_count = len(bill_ids)
        avg_bill = total_revenue / bill_count if bill_count else 0.0
        commission_rate = float(staff.commission_rate or 0)
        commission = total_revenue * (commission_rate / 100)
        incentive_threshold = float(getattr(staff, 'incentive_threshold', 50000.0) or 50000.0)
        incentive_rate = float(getattr(staff, 'incentive_rate', 0.0) or 0.0)
        incentive_base = max(total_revenue - incentive_threshold, 0.0) if incentive_rate > 0 else 0.0
        incentive_amount = incentive_base * (incentive_rate / 100)
        revenue_to_target = max(incentive_threshold - total_revenue, 0.0) if incentive_rate > 0 else 0.0
        target_progress = (total_revenue / incentive_threshold * 100) if incentive_threshold > 0 else 0.0
        variable_pay = commission + incentive_amount

        if incentive_rate <= 0:
            incentive_status = 'not_configured'
            guidance = 'Your incentive plan is not configured yet. Please check with your manager or owner.'
        elif incentive_amount > 0:
            incentive_status = 'earned'
            guidance = f'Target achieved. Every extra sale now adds {round(incentive_rate, 2)}% incentive.'
        else:
            incentive_status = 'target_not_met'
            guidance = f'Add {round(revenue_to_target, 2)} more performance revenue this period to start earning incentive.'

        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': period_days,
            },
            'staff': {
                'id': staff_id,
                'name': f"{staff.first_name or ''} {staff.last_name or ''}".strip() or 'Staff',
            },
            'performance': {
                'bill_count': bill_count,
                'item_count': item_count,
                'service_revenue': round(service_revenue, 2),
                'package_revenue': round(package_revenue, 2),
                'product_revenue': round(product_revenue, 2),
                'membership_revenue': round(membership_revenue, 2),
                'total_revenue': round(total_revenue, 2),
                'average_bill': round(avg_bill, 2),
            },
            'earnings': {
                'commission_rate': round(commission_rate, 2),
                'commission_earned': round(commission, 2),
                'incentive_threshold': round(incentive_threshold, 2),
                'incentive_rate': round(incentive_rate, 2),
                'incentive_base': round(incentive_base, 2),
                'incentive_amount': round(incentive_amount, 2),
                'revenue_to_target': round(revenue_to_target, 2),
                'target_progress_percent': round(target_progress, 2),
                'variable_pay': round(variable_pay, 2),
                'incentive_status': incentive_status,
                'guidance': guidance,
            },
            'calculation_note': (
                f"Commission: performance revenue x {round(commission_rate, 2)}%. "
                f"Incentive: max(performance revenue - target, 0) x {round(incentive_rate, 2)}%."
            )
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
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
        query = apply_branch_scope(query, branch, current_user)

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


@report_bp.route('/financial-overview', methods=['GET'])
@require_role('manager', 'owner')
def financial_overview(current_user=None):
    """Owner/manager profit-loss overview for the selected branch/date range."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date:
            start_date = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        start, end = get_ist_date_range(start_date, end_date)
        start_day = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_day = datetime.strptime(end_date, '%Y-%m-%d').date()
        period_days = max((end_day - start_day).days + 1, 1)

        branch = get_selected_branch(request, current_user)

        bills_query = Bill.objects(is_deleted=False, bill_date__gte=start, bill_date__lte=end)
        bills_query = apply_branch_scope(bills_query, branch, current_user)
        bills = list(bills_query)

        total_revenue = sum(float(b.final_amount or 0) for b in bills)
        subtotal = sum(float(b.subtotal or 0) for b in bills)
        discount_total = sum(float(b.discount_amount or 0) + float(getattr(b, 'referral_discount', 0) or 0) for b in bills)
        tax_total = sum(float(b.tax_amount or 0) for b in bills)
        card_fee_total = sum(float(getattr(b, 'card_fee_amount', 0) or 0) for b in bills)
        bill_count = len(bills)

        product_cost = 0.0
        product_revenue = 0.0
        service_revenue = 0.0
        membership_revenue = 0.0
        package_revenue = 0.0
        for bill in bills:
            for item in bill.items or []:
                item_total = float(item.total or 0)
                qty = int(item.quantity or 1)
                if item.item_type == 'product':
                    product_revenue += item_total
                    product_cost += _safe_product_cost(item) * qty
                elif item.item_type == 'service':
                    service_revenue += item_total
                elif item.item_type == 'package':
                    package_revenue += item_total
                elif item.item_type == 'membership':
                    membership_revenue += item_total

        expenses_query = Expense.objects(expense_date__gte=start_day, expense_date__lte=end_day)
        expenses_query = apply_branch_scope(expenses_query, branch, current_user)
        expenses = list(expenses_query)
        expense_total = sum(float(e.amount or 0) for e in expenses)

        staff_query = Staff.objects(status='active')
        staff_query = apply_branch_scope(staff_query, branch, current_user)
        monthly_salary_total = sum(float(s.salary or 0) for s in staff_query)
        salary_cost = monthly_salary_total * (period_days / 30.0)

        income_total = total_revenue
        outcome_total = expense_total + product_cost + salary_cost + tax_total
        net_profit = income_total - outcome_total

        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': period_days
            },
            'income': {
                'total_revenue': round(total_revenue, 2),
                'subtotal': round(subtotal, 2),
                'service_revenue': round(service_revenue, 2),
                'package_revenue': round(package_revenue, 2),
                'product_revenue': round(product_revenue, 2),
                'membership_revenue': round(membership_revenue, 2),
                'card_fee_collected': round(card_fee_total, 2),
            },
            'outcome': {
                'discount_total': round(discount_total, 2),
                'tax_total': round(tax_total, 2),
                'expense_total': round(expense_total, 2),
                'product_cost': round(product_cost, 2),
                'staff_salary_cost': round(salary_cost, 2),
                'total_outcome': round(outcome_total, 2),
            },
            'profit_loss': {
                'gross_profit_before_expenses': round(total_revenue - product_cost - tax_total, 2),
                'net_profit': round(net_profit, 2),
                'profit_margin_percent': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
                'expense_ratio_percent': round((expense_total / total_revenue * 100) if total_revenue > 0 else 0, 2),
                'discount_rate_percent': round((discount_total / subtotal * 100) if subtotal > 0 else 0, 2),
            },
            'activity': {
                'bills': bill_count,
                'average_bill_value': round(total_revenue / bill_count, 2) if bill_count else 0,
            }
        })
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


def _round_money(value):
    return round(float(value or 0), 2)


def _profit_status(net_profit):
    if net_profit > 0:
        return 'profit'
    if net_profit < 0:
        return 'loss'
    return 'break_even'


def _branch_info(branch):
    if not branch:
        return {
            'id': 'unassigned',
            'name': 'Unassigned',
            'city': None,
        }
    return {
        'id': str(branch.id),
        'name': branch.name or 'Unknown Branch',
        'city': branch.city,
    }


def _safe_branch_from_doc(doc):
    try:
        return doc.branch if getattr(doc, 'branch', None) else None
    except Exception:
        return None


def _safe_product_cost(item):
    try:
        snapshot_cost = getattr(item, 'cost_price', None)
        if snapshot_cost is not None:
            return float(snapshot_cost or 0)
        return float(item.product.cost or 0) if item.product else 0.0
    except Exception:
        return 0.0


def _append_decision(recommendations, category, title, message, priority='medium'):
    recommendations.append({
        'category': category,
        'title': title,
        'message': message,
        'priority': priority,
    })


@report_bp.route('/owner-financial-dashboard', methods=['GET'])
@require_role('owner')
def owner_financial_dashboard(current_user=None):
    """Owner branch-wise P&L, service/offer performance, income mix, and decision guidance."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date:
            start_date = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        start, end = get_ist_date_range(start_date, end_date)
        start_day = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_day = datetime.strptime(end_date, '%Y-%m-%d').date()
        period_days = max((end_day - start_day).days + 1, 1)

        selected_branch = get_selected_branch(request, current_user)

        if selected_branch:
            branch_docs = [selected_branch]
        else:
            branch_query = Branch.objects(is_active=True)
            demo_branch = get_demo_branch_exclusion(user=current_user, branch=None)
            if demo_branch:
                branch_query = branch_query.filter(id__ne=demo_branch.id)
            branch_docs = list(branch_query.order_by('name'))

        branch_summaries = {}
        for branch in branch_docs:
            info = _branch_info(branch)
            branch_summaries[info['id']] = {
                'branch_id': info['id'],
                'branch_name': info['name'],
                'branch_city': info['city'],
                'revenue': 0.0,
                'subtotal': 0.0,
                'discounts': 0.0,
                'tax': 0.0,
                'card_fee': 0.0,
                'expenses': 0.0,
                'product_cost': 0.0,
                'staff_salary_cost': 0.0,
                'total_cost': 0.0,
                'net_profit': 0.0,
                'profit_margin': 0.0,
                'bills': 0,
                'average_bill': 0.0,
                'status': 'break_even',
            }

        def ensure_branch(branch):
            info = _branch_info(branch)
            if info['id'] not in branch_summaries:
                branch_summaries[info['id']] = {
                    'branch_id': info['id'],
                    'branch_name': info['name'],
                    'branch_city': info['city'],
                    'revenue': 0.0,
                    'subtotal': 0.0,
                    'discounts': 0.0,
                    'tax': 0.0,
                    'card_fee': 0.0,
                    'expenses': 0.0,
                    'product_cost': 0.0,
                    'staff_salary_cost': 0.0,
                    'total_cost': 0.0,
                    'net_profit': 0.0,
                    'profit_margin': 0.0,
                    'bills': 0,
                    'average_bill': 0.0,
                    'status': 'break_even',
                }
            return branch_summaries[info['id']]

        bills_query = Bill.objects(is_deleted=False, bill_date__gte=start, bill_date__lte=end)
        bills_query = apply_branch_scope(bills_query, selected_branch, current_user)
        bills = list(bills_query)

        income_types = {
            'service': {'label': 'Services', 'amount': 0.0, 'count': 0},
            'product': {'label': 'Products', 'amount': 0.0, 'count': 0},
            'package': {'label': 'Packages', 'amount': 0.0, 'count': 0},
            'membership': {'label': 'Memberships', 'amount': 0.0, 'count': 0},
            'card_fee': {'label': 'Card Fees', 'amount': 0.0, 'count': 0},
        }
        payment_methods = {}
        service_stats = {}
        offer_stats = {}

        for bill in bills:
            branch_summary = ensure_branch(_safe_branch_from_doc(bill))
            bill_revenue = float(bill.final_amount or 0)
            bill_subtotal = float(bill.subtotal or 0)
            bill_discount = float(bill.discount_amount or 0) + float(getattr(bill, 'referral_discount', 0) or 0)
            bill_tax = float(bill.tax_amount or 0)
            bill_card_fee = float(getattr(bill, 'card_fee_amount', 0) or 0)

            branch_summary['revenue'] += bill_revenue
            branch_summary['subtotal'] += bill_subtotal
            branch_summary['discounts'] += bill_discount
            branch_summary['tax'] += bill_tax
            branch_summary['card_fee'] += bill_card_fee
            branch_summary['bills'] += 1

            if bill_card_fee:
                income_types['card_fee']['amount'] += bill_card_fee
                income_types['card_fee']['count'] += 1

            payment_mode = (bill.payment_mode or 'unknown').lower()
            payment_methods.setdefault(payment_mode, {
                'payment_mode': payment_mode.upper(),
                'amount': 0.0,
                'count': 0,
                'percentage': 0.0,
            })
            payment_methods[payment_mode]['amount'] += bill_revenue
            payment_methods[payment_mode]['count'] += 1

            offer = getattr(bill, 'applied_offer', None) or {}
            if offer and offer.get('name'):
                offer_key = str(offer.get('id') or offer.get('name'))
                offer_stats.setdefault(offer_key, {
                    'offer_id': str(offer.get('id') or ''),
                    'offer_name': offer.get('name') or 'Offer',
                    'offer_type': offer.get('type') or 'general',
                    'discount_percent': float(offer.get('percentage') or 0),
                    'bills': 0,
                    'revenue': 0.0,
                    'discount_given': 0.0,
                    'average_bill': 0.0,
                    'discount_rate': 0.0,
                    'decision': 'Monitor',
                })
                offer_stats[offer_key]['bills'] += 1
                offer_stats[offer_key]['revenue'] += bill_revenue
                offer_stats[offer_key]['discount_given'] += float(offer.get('amount') or bill_discount or 0)

            for item in bill.items or []:
                item_total = float(item.total or 0)
                item_qty = int(item.quantity or 1)
                item_type = item.item_type or 'other'

                if item_type in income_types:
                    income_types[item_type]['amount'] += item_total
                    income_types[item_type]['count'] += item_qty

                if item_type == 'product':
                    branch_summary['product_cost'] += _safe_product_cost(item) * item_qty

                if item_type == 'service':
                    service_name = item.name or 'Unknown Service'
                    try:
                        if item.service and item.service.name:
                            service_name = item.service.name
                    except Exception:
                        pass
                    service_stats.setdefault(service_name, {
                        'service_name': service_name,
                        'branch_name': branch_summary['branch_name'],
                        'quantity': 0,
                        'revenue': 0.0,
                        'estimated_profit': 0.0,
                        'average_price': 0.0,
                        'performance': 'monitor',
                        'decision': 'Monitor',
                    })
                    service_stats[service_name]['quantity'] += item_qty
                    service_stats[service_name]['revenue'] += item_total
                    service_stats[service_name]['estimated_profit'] += item_total

        expenses_query = Expense.objects(expense_date__gte=start_day, expense_date__lte=end_day)
        expenses_query = apply_branch_scope(expenses_query, selected_branch, current_user)
        for expense in expenses_query:
            branch_summary = ensure_branch(_safe_branch_from_doc(expense))
            branch_summary['expenses'] += float(expense.amount or 0)

        staff_query = Staff.objects(status='active')
        staff_query = apply_branch_scope(staff_query, selected_branch, current_user)
        for staff in staff_query:
            branch_summary = ensure_branch(_safe_branch_from_doc(staff))
            branch_summary['staff_salary_cost'] += float(staff.salary or 0) * (period_days / 30.0)

        for summary in branch_summaries.values():
            summary['total_cost'] = summary['expenses'] + summary['product_cost'] + summary['staff_salary_cost'] + summary['tax']
            summary['net_profit'] = summary['revenue'] - summary['total_cost']
            summary['average_bill'] = summary['revenue'] / summary['bills'] if summary['bills'] else 0
            summary['profit_margin'] = (summary['net_profit'] / summary['revenue'] * 100) if summary['revenue'] else 0
            summary['status'] = _profit_status(summary['net_profit'])

        branch_rows = sorted(branch_summaries.values(), key=lambda row: row['net_profit'], reverse=True)

        total_revenue = sum(row['revenue'] for row in branch_rows)
        total_cost = sum(row['total_cost'] for row in branch_rows)
        total_profit = total_revenue - total_cost
        total_discounts = sum(row['discounts'] for row in branch_rows)
        total_bills = sum(row['bills'] for row in branch_rows)
        total_income_mix = sum(item['amount'] for item in income_types.values()) or 1
        for item in income_types.values():
            item['percentage'] = (item['amount'] / total_income_mix * 100) if total_income_mix else 0

        for item in payment_methods.values():
            item['percentage'] = (item['amount'] / total_revenue * 100) if total_revenue else 0

        service_values = list(service_stats.values())
        average_service_revenue = (
            sum(row['revenue'] for row in service_values) / len(service_values)
            if service_values else 0
        )
        for row in service_values:
            row['average_price'] = row['revenue'] / row['quantity'] if row['quantity'] else 0
            if row['revenue'] >= average_service_revenue and row['quantity'] > 0:
                row['performance'] = 'strong'
                row['decision'] = 'Continue and promote'
            elif row['quantity'] <= 1 or row['revenue'] < average_service_revenue * 0.5:
                row['performance'] = 'underperforming'
                row['decision'] = 'Improve, reprice, or reduce focus'
            else:
                row['performance'] = 'monitor'
                row['decision'] = 'Monitor'

        offer_values = list(offer_stats.values())
        for row in offer_values:
            row['average_bill'] = row['revenue'] / row['bills'] if row['bills'] else 0
            gross_before_discount = row['revenue'] + row['discount_given']
            row['discount_rate'] = (row['discount_given'] / gross_before_discount * 100) if gross_before_discount else 0
            if row['revenue'] > 0 and row['discount_rate'] <= 15:
                row['decision'] = 'Continue'
            elif row['discount_rate'] > 30:
                row['decision'] = 'Review or reduce discount'
            else:
                row['decision'] = 'Monitor'

        recommendations = []
        if branch_rows:
            best = branch_rows[0]
            worst = branch_rows[-1]
            if best['revenue'] > 0:
                _append_decision(
                    recommendations,
                    'branch',
                    f"{best['branch_name']} is leading profit",
                    f"Net profit is {_round_money(best['net_profit'])} with {round(best['profit_margin'], 1)}% margin.",
                    'high'
                )
            if worst['net_profit'] < 0:
                _append_decision(
                    recommendations,
                    'branch',
                    f"{worst['branch_name']} is in loss",
                    "Review expenses, staff cost, discounts, and low-performing services for this branch.",
                    'high'
                )

        weak_services = [row for row in service_values if row['performance'] == 'underperforming']
        if weak_services:
            names = ', '.join(row['service_name'] for row in weak_services[:3])
            _append_decision(
                recommendations,
                'service',
                'Improve underperforming services',
                f"Review pricing, staff assignment, or promotion for: {names}.",
                'medium'
            )

        expensive_offers = [row for row in offer_values if row['discount_rate'] > 30]
        if expensive_offers:
            names = ', '.join(row['offer_name'] for row in expensive_offers[:3])
            _append_decision(
                recommendations,
                'offer',
                'Reduce high-discount offers',
                f"These offers give away more than 30% of their gross value: {names}.",
                'medium'
            )

        if total_revenue == 0:
            _append_decision(
                recommendations,
                'business',
                'No revenue in selected period',
                'Use a wider date range or verify bill checkout activity for this branch selection.',
                'medium'
            )

        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': period_days,
            },
            'summary': {
                'total_revenue': _round_money(total_revenue),
                'total_cost': _round_money(total_cost),
                'net_profit': _round_money(total_profit),
                'profit_margin': round((total_profit / total_revenue * 100) if total_revenue else 0, 2),
                'total_discounts': _round_money(total_discounts),
                'bills': total_bills,
                'average_bill': _round_money(total_revenue / total_bills) if total_bills else 0,
                'status': _profit_status(total_profit),
            },
            'branch_summaries': [
                {
                    **row,
                    'revenue': _round_money(row['revenue']),
                    'subtotal': _round_money(row['subtotal']),
                    'discounts': _round_money(row['discounts']),
                    'tax': _round_money(row['tax']),
                    'card_fee': _round_money(row['card_fee']),
                    'expenses': _round_money(row['expenses']),
                    'product_cost': _round_money(row['product_cost']),
                    'staff_salary_cost': _round_money(row['staff_salary_cost']),
                    'total_cost': _round_money(row['total_cost']),
                    'net_profit': _round_money(row['net_profit']),
                    'average_bill': _round_money(row['average_bill']),
                    'profit_margin': round(row['profit_margin'], 2),
                }
                for row in branch_rows
            ],
            'service_performance': sorted(
                [
                    {
                        **row,
                        'revenue': _round_money(row['revenue']),
                        'estimated_profit': _round_money(row['estimated_profit']),
                        'average_price': _round_money(row['average_price']),
                    }
                    for row in service_values
                ],
                key=lambda row: row['revenue'],
                reverse=True
            )[:10],
            'offer_performance': sorted(
                [
                    {
                        **row,
                        'revenue': _round_money(row['revenue']),
                        'discount_given': _round_money(row['discount_given']),
                        'average_bill': _round_money(row['average_bill']),
                        'discount_rate': round(row['discount_rate'], 2),
                    }
                    for row in offer_values
                ],
                key=lambda row: row['revenue'],
                reverse=True
            )[:10],
            'income_analysis': {
                'by_type': [
                    {
                        **item,
                        'amount': _round_money(item['amount']),
                        'percentage': round(item['percentage'], 2),
                    }
                    for item in income_types.values()
                    if item['amount'] > 0
                ],
                'payment_methods': sorted(
                    [
                        {
                            **item,
                            'amount': _round_money(item['amount']),
                            'percentage': round(item['percentage'], 2),
                        }
                        for item in payment_methods.values()
                    ],
                    key=lambda row: row['amount'],
                    reverse=True
                ),
            },
            'branch_comparison': {
                'best_branch': branch_rows[0] if branch_rows else None,
                'worst_branch': branch_rows[-1] if branch_rows else None,
            },
            'recommendations': recommendations,
        })
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
        query = apply_branch_scope(query, None, None)

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
        query = apply_branch_scope(query, None, None)

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
        bills_query = Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        bills_query = apply_branch_scope(bills_query, None, None)
        bills = list(bills_query)

        # Group bills by month
        monthly_revenue = {}
        for bill in bills:
            month_key = bill.bill_date.strftime('%Y-%m')
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = {'revenue': 0, 'bills': 0}
            monthly_revenue[month_key]['revenue'] += bill.final_amount or 0
            monthly_revenue[month_key]['bills'] += 1

        # Get all expenses in date range - force evaluation
        expenses_query = Expense.objects.filter(
            expense_date__gte=start.date(),
            expense_date__lte=end.date()
        )
        expenses_query = apply_branch_scope(expenses_query, None, None)
        expenses = list(expenses_query)

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
@require_role('manager', 'owner')
def staff_performance_analysis(current_user=None):
    """Staff performance analysis - OPTIMIZED with aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Use proper IST-to-UTC date conversion
        if start_date and end_date:
            start, end = get_ist_date_range(start_date, end_date)
        elif start_date:
            start, end = get_ist_date_range(start_date, datetime.now().strftime('%Y-%m-%d'))
        else:
            default_start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            default_end = datetime.now().strftime('%Y-%m-%d')
            start, end = get_ist_date_range(default_start, default_end)

        branch = get_selected_branch(request, current_user)
        
        # Revenue is allocated proportionally from each bill's final_amount
        # (cash collected) — see utils/staff_revenue.py — so totals here
        # reconcile with the dashboard and Cash Register.
        # Company-wide means all production branches, excluding the demo branch.
        match_stage = {
            "is_deleted": False,
            "bill_date": {"$gte": start, "$lte": end},
        }
        apply_branch_scope_to_match(match_stage, branch, current_user)

        pipeline = attributed_revenue_pipeline(match_stage) + [
            {"$match": {"items.staff": {"$ne": None}}},
            {"$group": {
                "_id": "$items.staff",
                "total_revenue": {"$sum": "$_attributed_revenue"},
                "item_count": {"$sum": {"$ifNull": ["$items.quantity", 1]}},
                "service_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "service"]},
                            "$_attributed_revenue",
                            0
                        ]
                    }
                },
                "package_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "package"]},
                            "$_attributed_revenue",
                            0
                        ]
                    }
                },
                "product_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "product"]},
                            "$_attributed_revenue",
                            0
                        ]
                    }
                },
                "membership_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "membership"]},
                            "$_attributed_revenue",
                            0
                        ]
                    }
                },
                "service_items": {
                    "$push": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "service"]},
                            {
                                "service_id": "$items.service",
                                "quantity": {"$ifNull": ["$items.quantity", 1]},
                                "revenue": "$_attributed_revenue"
                            },
                            "$$REMOVE"
                        ]
                    }
                }
            }},
            {"$lookup": {
                "from": "staffs",
                "localField": "_id",
                "foreignField": "_id",
                "as": "staff_doc"
            }},
            {"$unwind": {"path": "$staff_doc", "preserveNullAndEmptyArrays": True}},
            # Note: dropped staff_doc.status='active' filter — historical
            # revenue from inactive staff must still appear in reports.
            {"$project": {
                "staff_id": {"$toString": "$_id"},
                "staff_name": {
                    "$trim": {
                        "input": {
                            "$concat": [
                                {"$ifNull": ["$staff_doc.first_name", ""]},
                                " ",
                                {"$ifNull": ["$staff_doc.last_name", ""]}
                            ]
                        }
                    }
                },
                "staff_status": {"$ifNull": ["$staff_doc.status", None]},
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "item_count": 1,
                "service_revenue": {"$round": ["$service_revenue", 2]},
                "package_revenue": {"$round": ["$package_revenue", 2]},
                "product_revenue": {"$round": ["$product_revenue", 2]},
                "membership_revenue": {"$round": ["$membership_revenue", 2]},
                "service_items": 1
            }}
        ]

        # Execute aggregation
        staff_performance_results = list(Bill.objects.aggregate(pipeline))

        # Get service IDs for service breakdown lookup
        service_ids = set()
        for result in staff_performance_results:
            for item in result.get('service_items', []):
                if item and item.get('service_id'):
                    service_ids.add(item['service_id'])

        # Batch lookup services and their groups
        service_group_map = {}
        if service_ids:
            services_pipeline = [
                {"$match": {"_id": {"$in": list(service_ids)}}},
                {"$lookup": {
                    "from": "service_groups",
                    "localField": "group",
                    "foreignField": "_id",
                    "as": "group_doc"
                }},
                {"$unwind": {"path": "$group_doc", "preserveNullAndEmptyArrays": True}},
                {"$project": {
                    "service_id": {"$toString": "$_id"},
                    "group_name": {"$ifNull": ["$group_doc.name", "Other"]}
                }}
            ]
            from models import Service
            service_groups = list(Service.objects.aggregate(services_pipeline))
            service_group_map = {s['service_id']: s['group_name'] for s in service_groups}

        # Build performance list with service breakdown
        performance = []
        staff_names_with_revenue = set()
        for result in staff_performance_results:
            # Calculate service breakdown by group
            service_breakdown = {}
            for item in result.get('service_items', []):
                if not item or not item.get('service_id'):
                    continue

                service_id = str(item['service_id'])
                group_name = service_group_map.get(service_id, 'Other')

                if group_name not in service_breakdown:
                    service_breakdown[group_name] = {'count': 0, 'revenue': 0.0}

                service_breakdown[group_name]['count'] += item.get('quantity', 1)
                service_breakdown[group_name]['revenue'] += item.get('revenue', 0.0)

            # Round service breakdown values
            for group_name in service_breakdown:
                service_breakdown[group_name]['revenue'] = round(service_breakdown[group_name]['revenue'], 2)

            total_revenue = result.get('total_revenue', 0.0)
            item_count = result.get('item_count', 0)
            staff_name = result.get('staff_name', '').strip()
            staff_names_with_revenue.add(result.get('staff_id', ''))

            performance.append({
                'staff_name': staff_name,
                'staff_status': result.get('staff_status'),
                'total_revenue': total_revenue,
                'total_services': int(item_count),
                'service_revenue': result.get('service_revenue', 0.0),
                'package_revenue': result.get('package_revenue', 0.0),
                'product_revenue': result.get('product_revenue', 0.0),
                'membership_revenue': result.get('membership_revenue', 0.0),
                'service_breakdown': service_breakdown,
                'average_per_service': round(total_revenue / item_count, 2) if item_count > 0 else 0
            })

        # Include all active staff in the selected branch (even those with zero revenue in this period)
        from models import Staff as StaffModel
        all_active_staff_query = StaffModel.objects(status='active')
        all_active_staff_query = apply_branch_scope(all_active_staff_query, branch, current_user)
        all_active_staff = list(all_active_staff_query)
        
        for staff in all_active_staff:
            if str(staff.id) not in staff_names_with_revenue:
                name = f"{staff.first_name or ''} {staff.last_name or ''}".strip()
                performance.append({
                    'staff_name': name,
                    'staff_status': 'active',
                    'total_revenue': 0.0,
                    'total_services': 0,
                    'service_revenue': 0.0,
                    'package_revenue': 0.0,
                    'product_revenue': 0.0,
                    'membership_revenue': 0.0,
                    'service_breakdown': {},
                    'average_per_service': 0
                })

        # Sort by total revenue
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
        bills_query = Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        bills_query = apply_branch_scope(bills_query, None, None)
        bills = list(bills_query)
        total_revenue = sum(bill.final_amount or 0 for bill in bills)
        total_bills = len(bills)

        # Expenses - force evaluation
        expenses_query = Expense.objects.filter(
            expense_date__gte=start.date(),
            expense_date__lte=end.date()
        )
        expenses_query = apply_branch_scope(expenses_query, None, None)
        expenses = list(expenses_query)
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
        appointments_query = Appointment.objects.filter(
            appointment_date__gte=start.date(),
            appointment_date__lte=end.date()
        )
        appointments_query = apply_branch_scope(appointments_query, None, None)
        appointments = appointments_query.count()

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
