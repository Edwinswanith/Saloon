from flask import Blueprint, request, jsonify
from models import Customer, Bill, Membership, ReferralProgramSettings, Referral
from datetime import datetime, timedelta
from mongoengine import Q
from mongoengine.errors import NotUniqueError
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import (
    apply_branch_scope,
    apply_branch_scope_to_match,
    get_selected_branch,
    filter_by_branch,
)
import random
import string

customer_bp = Blueprint('customers', __name__)

@customer_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

def generate_referral_code(first_name):
    """Generate referral code from customer name"""
    name_part = first_name.upper()[:5] if first_name else 'CUST'
    random_part = ''.join(random.choices(string.digits, k=3))
    return f"{name_part}{random_part}"


def _visit_range_start(value):
    today = datetime.utcnow()
    ranges = {
        'last_week': today - timedelta(days=7),
        'last_month': today - timedelta(days=30),
        'last_year': today - timedelta(days=365),
    }
    return ranges.get(value)


def _safe_item_service_info(item, fallback_name='Service'):
    service = getattr(item, 'service', None)
    service_id = None
    group_name = 'General'
    service_name = fallback_name

    try:
        if service:
            service_id = str(service.id)
            service_name = getattr(service, 'name', None) or fallback_name
            if getattr(service, 'group', None):
                group_name = service.group.name or 'General'
    except Exception:
        pass

    return service_id, service_name, group_name


def _days_since(value):
    if not value:
        return None
    try:
        compare_date = value.date() if hasattr(value, 'date') else value
        return max((datetime.utcnow().date() - compare_date).days, 0)
    except Exception:
        return None


def _average_visit_gap_days(visits):
    visit_dates = []
    for visit in visits:
        raw_date = visit.get('bill_date')
        if not raw_date:
            continue
        try:
            visit_dates.append(datetime.fromisoformat(raw_date).date())
        except Exception:
            continue

    unique_dates = sorted(set(visit_dates))
    if len(unique_dates) < 2:
        return None

    gaps = [
        (unique_dates[index] - unique_dates[index - 1]).days
        for index in range(1, len(unique_dates))
        if (unique_dates[index] - unique_dates[index - 1]).days >= 0
    ]
    if not gaps:
        return None
    return round(sum(gaps) / len(gaps), 1)


def _build_history_insights(services, group_map, visits):
    visit_count = len(visits)
    service_count = sum(service.get('count', 0) for service in services)
    avg_gap = _average_visit_gap_days(visits)
    last_visit_days = _days_since(datetime.fromisoformat(visits[0]['bill_date']) if visits and visits[0].get('bill_date') else None)

    preferred_groups = sorted(
        group_map.values(),
        key=lambda row: (row.get('count', 0), row.get('revenue', 0)),
        reverse=True
    )
    for group in preferred_groups:
        group['revenue'] = round(group.get('revenue', 0), 2)
        group['services'] = sorted(group.get('services', []))[:5]

    recommendations = []
    top_services = services[:3]
    for index, service in enumerate(top_services):
        confidence = min(95, 45 + (service.get('count', 0) * 12))
        recommendations.append({
            'type': 'repeat_service',
            'priority': 'high' if index == 0 and service.get('count', 0) >= 2 else 'medium',
            'service_id': service.get('service_id'),
            'service_name': service.get('name'),
            'category': service.get('group_name') or 'General',
            'title': f"Suggest {service.get('name')}",
            'reason': f"Taken {service.get('count', 0)} time(s), total spend ₹{service.get('revenue', 0):,.0f}.",
            'confidence': confidence,
        })

    if preferred_groups:
        top_group = preferred_groups[0]
        recommendations.append({
            'type': 'category_preference',
            'priority': 'high' if top_group.get('count', 0) >= 3 else 'medium',
            'service_id': None,
            'service_name': None,
            'category': top_group.get('name'),
            'title': f"Customer prefers {top_group.get('name')}",
            'reason': f"{top_group.get('count', 0)} service(s) from this category. Good area to start consultation.",
            'confidence': min(90, 40 + (top_group.get('count', 0) * 10)),
        })

    if last_visit_days is not None and last_visit_days >= 45:
        recommendations.append({
            'type': 'returning_after_gap',
            'priority': 'medium',
            'service_id': top_services[0].get('service_id') if top_services else None,
            'service_name': top_services[0].get('name') if top_services else None,
            'category': top_services[0].get('group_name') if top_services else None,
            'title': 'Re-engage gently',
            'reason': f"Last visit was {last_visit_days} days ago. Start with their known preference and ask about current needs.",
            'confidence': 70,
        })

    if not recommendations:
        recommendations.append({
            'type': 'new_customer',
            'priority': 'low',
            'service_id': None,
            'service_name': None,
            'category': None,
            'title': 'Build preference profile',
            'reason': 'No completed service history yet. Ask about concerns, goals, and preferred staff/service type.',
            'confidence': 40,
        })

    return {
        'preferred_service': top_services[0] if top_services else None,
        'preferred_category': preferred_groups[0] if preferred_groups else None,
        'preferred_categories': preferred_groups[:5],
        'average_visit_gap_days': avg_gap,
        'last_visit_days_ago': last_visit_days,
        'service_count': service_count,
        'visit_count': visit_count,
        'recommendations': recommendations[:5],
    }


def _customer_stats_map(customer_ids, branch, current_user):
    if not customer_ids:
        return {}

    match_stage = {
        "customer": {"$in": [ObjectId(str(cid)) for cid in customer_ids]},
        "is_deleted": False,
    }
    apply_branch_scope_to_match(match_stage, branch, current_user)

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$customer",
            "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}},
            "total_visits": {"$sum": 1},
            "last_visit": {"$max": "$bill_date"}
        }}
    ]
    stats = {}
    for row in Bill.objects.aggregate(pipeline):
        stats[str(row['_id'])] = {
            'total_revenue': row.get('total_revenue', 0) or 0,
            'total_visits': row.get('total_visits', 0) or 0,
            'last_visit': row.get('last_visit')
        }
    return stats


def _bill_customer_ids(branch, current_user, since=None, sort_by=None, limit=None):
    match_stage = {"is_deleted": False, "customer": {"$ne": None}}
    if since:
        match_stage["bill_date"] = {"$gte": since}
    apply_branch_scope_to_match(match_stage, branch, current_user)

    group = {
        "_id": "$customer",
        "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}},
        "total_visits": {"$sum": 1},
        "last_visit": {"$max": "$bill_date"},
    }
    pipeline = [{"$match": match_stage}, {"$group": group}]
    if sort_by == 'revenue':
        pipeline.append({"$sort": {"total_revenue": -1}})
    elif sort_by == 'visits':
        pipeline.append({"$sort": {"total_visits": -1}})
    elif sort_by == 'last_visit':
        pipeline.append({"$sort": {"last_visit": -1}})
    if limit:
        pipeline.append({"$limit": int(limit)})

    return [row['_id'] for row in Bill.objects.aggregate(pipeline) if row.get('_id')]

@customer_bp.route('/', methods=['GET'])
@require_auth
def get_customers(current_user=None):
    """Get all customers with optional search, branch filtering, and filters"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    source_filter = request.args.get('source', '')
    gender_filter = request.args.get('gender', '')
    dob_range_filter = request.args.get('dob_range', '')
    visit_range_filter = request.args.get('visit_range', '')
    segment_filter = request.args.get('segment', '')
    
    # Get branch for filtering
    # If branch is selected (via X-Branch-Id header), filter by that branch
    # If no branch is selected (Owner without branch selection), show all customers
    branch = get_selected_branch(request, current_user)
    query = Customer.objects.filter(merged_into=None)

    query = apply_branch_scope(query, branch, current_user)
    
    # Apply source filter
    if source_filter:
        query = query.filter(source=source_filter)
    
    # Apply gender filter
    if gender_filter:
        query = query.filter(gender=gender_filter)
    
    # Apply DOB range filter
    if dob_range_filter:
        query = query.filter(dob_range=dob_range_filter)

    if visit_range_filter:
        since = _visit_range_start(visit_range_filter)
        if since:
            query = query.filter(id__in=_bill_customer_ids(branch, current_user, since=since))

    if segment_filter == 'top_revenue':
        query = query.filter(id__in=_bill_customer_ids(branch, current_user, sort_by='revenue', limit=10))
    elif segment_filter == 'top_visits':
        query = query.filter(id__in=_bill_customer_ids(branch, current_user, sort_by='visits', limit=10))
    elif segment_filter == 'inactive_60':
        cutoff = datetime.utcnow() - timedelta(days=60)
        recent_ids = set(str(cid) for cid in _bill_customer_ids(branch, current_user, since=cutoff))
        if recent_ids:
            query = query.filter(id__nin=[ObjectId(cid) for cid in recent_ids])
    
    if search:
        query = query.filter(
            Q(mobile__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Apply sorting for consistent pagination
    query = query.order_by('-created_at')
    
    total = query.count()
    # Force evaluation by converting to list
    customers = list(query.skip((page - 1) * per_page).limit(per_page))
    stats_map = _customer_stats_map([c.id for c in customers], branch, current_user)
    
    return jsonify({
        'customers': [{
            'id': str(c.id),
            'mobile': c.mobile,
            'firstName': c.first_name,
            'lastName': c.last_name,
            'email': c.email,
            'source': c.source,
            'gender': c.gender,
            'dobRange': c.dob_range,
            'referralCode': c.referral_code,
            'totalVisits': stats_map.get(str(c.id), {}).get('total_visits', 0),
            'totalRevenue': round(stats_map.get(str(c.id), {}).get('total_revenue', 0), 2),
            'lastVisit': stats_map.get(str(c.id), {}).get('last_visit').isoformat() if stats_map.get(str(c.id), {}).get('last_visit') else None
        } for c in customers],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@customer_bp.route('/<customer_id>', methods=['GET'])
@require_auth
def get_customer(customer_id, current_user=None):
    """Get single customer by ID with visit history"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        query = apply_branch_scope(query, branch, current_user)
        customer = query.first()
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # OPTIMIZED: Calculate visit history and revenue using aggregation
        from bson import ObjectId
        match_stage = {
            "customer": ObjectId(customer_id),
            "is_deleted": False
        }
        apply_branch_scope_to_match(match_stage, branch, current_user)
        
        bills_pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}},
                "total_visits": {"$sum": 1},
                "last_visit": {"$max": "$bill_date"}
            }}
        ]
        
        bills_result = list(Bill.objects.aggregate(bills_pipeline))
        
        if bills_result:
            total_visits = bills_result[0].get('total_visits', 0)
            total_revenue = bills_result[0].get('total_revenue', 0.0)
            last_visit = bills_result[0].get('last_visit')
        else:
            total_visits = 0
            total_revenue = 0.0
            last_visit = None
        
        # Get last service from most recent bill
        last_service = None
        latest_bill = Bill.objects(__raw__=match_stage).order_by('-bill_date').first()
        if latest_bill:
            for item in latest_bill.items or []:
                if item.item_type in ('service', 'package') and item.name:
                    last_service = item.name
                    break
        
        # Get active membership info
        active_membership = Membership.objects(
            customer=customer,
            status='active',
            expiry_date__gte=datetime.utcnow()
        ).first()
        
        membership_data = None
        if active_membership:
            membership_data = {
                'id': str(active_membership.id),
                'name': active_membership.name,
                'plan': {
                    'id': str(active_membership.plan.id) if active_membership.plan else None,
                    'name': active_membership.plan.name if active_membership.plan else None,
                    'allocated_discount': active_membership.plan.allocated_discount if active_membership.plan else 0.0
                } if active_membership.plan else None,
                'purchase_date': active_membership.purchase_date.isoformat() if active_membership.purchase_date else None,
                'expiry_date': active_membership.expiry_date.isoformat() if active_membership.expiry_date else None,
                'status': active_membership.status
            }
        
        response = jsonify({
            'id': str(customer.id),
            'mobile': customer.mobile,
            'firstName': customer.first_name,
            'lastName': customer.last_name,
            'email': customer.email,
            'source': customer.source,
            'gender': customer.gender,
            'dob': customer.dob.isoformat() if customer.dob else None,
            'dobRange': customer.dob_range,
            'referralCode': customer.referral_code,
            'referredBy': str(customer._data.get('referred_by')) if customer._data.get('referred_by') else None,
            'referralRewardUsed': getattr(customer, 'referral_reward_used', False),
            'membership': membership_data,
            'last_visit': last_visit.isoformat() if last_visit else None,
            'total_visits': total_visits,
            'total_revenue': total_revenue,
            'last_service': last_service,
            'notes': getattr(customer, 'notes', 'N/A')
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        print(f"Error fetching customer details: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@customer_bp.route('/<customer_id>/history', methods=['GET'])
@require_auth
def get_customer_history(customer_id, current_user=None):
    """Get visit and service history for one customer."""
    try:
        if not ObjectId.is_valid(customer_id):
            return jsonify({'error': 'Invalid customer ID format'}), 400

        branch = get_selected_branch(request, current_user)
        customer_query = Customer.objects(id=customer_id, merged_into=None)
        customer_query = apply_branch_scope(customer_query, branch, current_user)
        customer = customer_query.first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        match_stage = {
            "customer": ObjectId(customer_id),
            "is_deleted": False,
        }
        apply_branch_scope_to_match(match_stage, branch, current_user)
        bills = list(Bill.objects(__raw__=match_stage).order_by('-bill_date').limit(100))

        service_map = {}
        group_map = {}
        visits = []
        for bill in bills:
            items = []
            for item in bill.items or []:
                item_name = item.name or 'Item'
                item_type = item.item_type or 'item'
                quantity = int(item.quantity or 1)
                amount = float(item.total or 0)
                service_id = None
                group_name = None

                if item_type in ('service', 'package'):
                    service_id, resolved_name, group_name = _safe_item_service_info(item, item_name)
                    if resolved_name:
                        item_name = resolved_name

                items.append({
                    'type': item_type,
                    'name': item_name,
                    'quantity': quantity,
                    'amount': round(amount, 2),
                    'service_id': service_id,
                    'group_name': group_name,
                    'staff_name': f"{item.staff.first_name} {item.staff.last_name}".strip() if item.staff else None
                })

                if item_type in ('service', 'package'):
                    service_key = service_id or item_name
                    if service_key not in service_map:
                        service_map[service_key] = {
                            'service_id': service_id,
                            'name': item_name,
                            'group_name': group_name or 'General',
                            'count': 0,
                            'revenue': 0.0,
                            'last_visit': None,
                        }
                    service_map[service_key]['count'] += quantity
                    service_map[service_key]['revenue'] += amount
                    if bill.bill_date and (
                        not service_map[service_key]['last_visit'] or
                        bill.bill_date.isoformat() > service_map[service_key]['last_visit']
                    ):
                        service_map[service_key]['last_visit'] = bill.bill_date.isoformat()

                    group_key = group_name or 'General'
                    if group_key not in group_map:
                        group_map[group_key] = {
                            'name': group_key,
                            'count': 0,
                            'revenue': 0.0,
                            'services': set(),
                        }
                    group_map[group_key]['count'] += quantity
                    group_map[group_key]['revenue'] += amount
                    group_map[group_key]['services'].add(item_name)

            visits.append({
                'bill_id': str(bill.id),
                'bill_number': bill.bill_number,
                'bill_date': bill.bill_date.isoformat() if bill.bill_date else None,
                'final_amount': round(float(bill.final_amount or 0), 2),
                'payment_mode': bill.payment_mode,
                'items': items,
            })

        total_revenue = sum(v['final_amount'] for v in visits)
        services = sorted(service_map.values(), key=lambda row: row['count'], reverse=True)
        for service in services:
            service['revenue'] = round(service['revenue'], 2)
            service['visit_share'] = round((service['count'] / max(sum(row['count'] for row in services), 1)) * 100, 1)

        insights = _build_history_insights(services, group_map, visits)

        return jsonify({
            'customer': {
                'id': str(customer.id),
                'name': f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
                'mobile': customer.mobile,
                'email': customer.email,
            },
            'summary': {
                'visit_count': len(visits),
                'total_revenue': round(total_revenue, 2),
                'last_visit': visits[0]['bill_date'] if visits else None,
                'service_count': sum(service['count'] for service in services),
            },
            'services': services,
            'preferences': insights,
            'recommendations': insights.get('recommendations', []),
            'visits': visits,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/', methods=['POST'])
@require_auth
def create_customer(current_user=None):
    """Create new customer (branch-scoped uniqueness)"""
    try:
        data = request.json

        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if not data.get('mobile'):
            response = jsonify({'error': 'Mobile number is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        if not data.get('firstName'):
            response = jsonify({'error': 'First name is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required. Please ensure you have selected a branch or your user has a branch assigned.'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        mobile = data.get('mobile')

        # Check if customer exists in THIS branch → reuse existing
        existing_same_branch = Customer.objects(mobile=mobile, branch=branch).first()
        if existing_same_branch:
            customer_name = f'{existing_same_branch.first_name} {existing_same_branch.last_name}'.strip()
            response = jsonify({
                'id': str(existing_same_branch.id),
                'created': False,
                'reason': 'existing_same_branch',
                'message': f'Customer with mobile {mobile} already exists in this branch',
                'customerName': customer_name
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        # Customer may exist in OTHER branches — that's fine, create in this branch

        # Handle DOB if provided
        dob = None
        if data.get('dob'):
            try:
                dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            except ValueError:
                response = jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400

        # Look up referrer if referral code provided
        referrer = None
        applied_referral_code = data.get('referralCode', '').strip()
        if applied_referral_code:
            settings = ReferralProgramSettings.get_settings()
            if settings.enabled:
                referrer = Customer.objects(referral_code=applied_referral_code).first()

        customer = Customer(
            mobile=mobile,
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('email', ''),
            source=data.get('source', 'Walk-in') if not referrer else 'Referral',
            gender=data.get('gender', ''),
            dob=dob,
            dob_range=data.get('dobRange', ''),
            referral_code=generate_referral_code(data.get('firstName', '')),
            referred_by=referrer,
            branch=branch
        )
        customer.save()

        # Create referral tracking record
        referral_created = False
        if referrer:
            try:
                ref = Referral(
                    referrer=referrer,
                    referee=customer,
                    branch=branch
                )
                ref.save()
                referral_created = True
            except Exception as e:
                print(f"[CUSTOMER CREATE] Warning: Failed to create referral record: {e}")

        response = jsonify({
            'id': str(customer.id),
            'created': True,
            'reason': 'created_new',
            'message': 'Customer created successfully',
            'referralApplied': referral_created
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201

    except NotUniqueError as e:
        error_str = str(e).lower()
        # Check if it's a mobile+branch duplicate (race condition)
        existing = Customer.objects(mobile=data.get('mobile'), branch=branch).first()
        if existing:
            customer_name = f'{existing.first_name} {existing.last_name}'.strip()
            response = jsonify({
                'id': str(existing.id),
                'created': False,
                'reason': 'existing_same_branch',
                'message': f'Customer with mobile {data.get("mobile")} already exists in this branch',
                'customerName': customer_name
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        # If it's a referral_code collision, retry with a new code
        if 'referral_code' in error_str:
            try:
                customer.referral_code = generate_referral_code(data.get('firstName', ''))
                customer.save()
                response = jsonify({
                    'id': str(customer.id),
                    'created': True,
                    'reason': 'created_new',
                    'message': 'Customer created successfully'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 201
            except Exception:
                pass
        response = jsonify({'error': 'Could not create customer. Please try again.'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        print(f"[CUSTOMER CREATE] Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@customer_bp.route('/bulk', methods=['POST'])
@require_auth
def bulk_create_customers(current_user=None):
    """Batch-create customers from CSV import. Skips duplicates within the
    current branch (one query) and bulk-inserts the rest (one round-trip)."""
    try:
        payload = request.json or {}
        rows = payload.get('customers') or payload.get('rows') or []
        if not isinstance(rows, list) or not rows:
            response = jsonify({'error': 'customers array is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        def _pick(row, *keys):
            for k in keys:
                v = row.get(k)
                if v is not None and str(v).strip():
                    return str(v).strip()
            return ''

        valid = []
        errors = []
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append({'row': idx + 1, 'error': 'not an object'})
                continue
            mobile = _pick(row, 'mobile')
            first_name = _pick(row, 'firstName', 'first_name')
            if not mobile:
                errors.append({'row': idx + 1, 'error': 'mobile required'})
                continue
            if not first_name:
                errors.append({'row': idx + 1, 'error': 'firstName required'})
                continue
            valid.append({
                'mobile': mobile,
                'first_name': first_name,
                'last_name': _pick(row, 'lastName', 'last_name'),
                'email': _pick(row, 'email'),
                'source': _pick(row, 'source') or 'Walk-in',
                'gender': _pick(row, 'gender'),
                'dob_range': _pick(row, 'dobRange', 'dob_range'),
            })

        mobiles = [r['mobile'] for r in valid]
        existing_mobiles = set()
        if mobiles:
            for c in Customer.objects(mobile__in=mobiles, branch=branch).only('mobile'):
                existing_mobiles.add(c.mobile)

        to_insert = []
        skipped = []
        for r in valid:
            if r['mobile'] in existing_mobiles:
                skipped.append({'mobile': r['mobile'], 'reason': 'already_exists_in_branch'})
                continue
            to_insert.append(Customer(
                mobile=r['mobile'],
                first_name=r['first_name'],
                last_name=r['last_name'],
                email=r['email'],
                source=r['source'],
                gender=r['gender'],
                dob_range=r['dob_range'],
                referral_code=generate_referral_code(r['first_name']),
                branch=branch,
            ))

        created_count = 0
        if to_insert:
            try:
                Customer.objects.insert(to_insert, load_bulk=False)
                created_count = len(to_insert)
            except NotUniqueError:
                for c in to_insert:
                    try:
                        c.save()
                        created_count += 1
                    except NotUniqueError:
                        try:
                            c.referral_code = generate_referral_code(c.first_name)
                            c.save()
                            created_count += 1
                        except Exception as e2:
                            errors.append({'mobile': c.mobile, 'error': f'save_failed: {e2}'})
                    except Exception as e3:
                        errors.append({'mobile': c.mobile, 'error': str(e3)})

        response = jsonify({
            'created': created_count,
            'skipped': len(skipped),
            'errors': errors,
            'skipped_details': skipped,
            'total_received': len(rows),
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"[CUSTOMER BULK] Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@customer_bp.route('/<customer_id>', methods=['PUT'])
@require_auth
def update_customer(customer_id, current_user=None):
    """Update customer"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        query = apply_branch_scope(query, branch, current_user)
        customer = query.first()
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        data = request.json
        if not data:
            response = jsonify({'error': 'No data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if 'firstName' in data:
            customer.first_name = data['firstName']
        if 'lastName' in data:
            customer.last_name = data['lastName']
        if 'email' in data:
            customer.email = data['email']
        if 'source' in data:
            customer.source = data['source']
        if 'gender' in data:
            customer.gender = data['gender']
        if 'dobRange' in data:
            customer.dob_range = data['dobRange']
        customer.updated_at = datetime.utcnow()
        
        if data.get('dob'):
            try:
                customer.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            except ValueError:
                response = jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
        
        customer.save()
        response = jsonify({'message': 'Customer updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/<customer_id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_customer(customer_id, current_user=None):
    """Delete customer (manager/owner only)"""
    try:
        from bson import ObjectId
        if not ObjectId.is_valid(customer_id):
            return jsonify({'error': 'Invalid customer ID format'}), 400
        customer = Customer.objects.get(id=customer_id)
        customer.delete()
        response = jsonify({'message': 'Customer deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/<customer_id>/active-membership', methods=['GET'])
@require_auth
def get_customer_active_membership(customer_id, current_user=None):
    """Get customer's active membership with plan details"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Customer.objects(id=customer_id)
        query = apply_branch_scope(query, branch, current_user)
        customer = query.first()
        
        if not customer:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # Get active membership (status='active' and expiry_date >= today)
        membership_query = Membership.objects(
            customer=customer,
            status='active',
            expiry_date__gte=datetime.utcnow()
        )
        membership_query = apply_branch_scope(membership_query, branch, current_user)
        
        active_membership = membership_query.first()
        
        if not active_membership:
            response = jsonify({
                'active': False,
                'membership': None
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        
        # Return membership with plan details
        membership_data = {
            'id': str(active_membership.id),
            'name': active_membership.name,
            'purchase_date': active_membership.purchase_date.isoformat() if active_membership.purchase_date else None,
            'expiry_date': active_membership.expiry_date.isoformat() if active_membership.expiry_date else None,
            'status': active_membership.status,
            'plan': None
        }
        
        if active_membership.plan:
            plan = active_membership.plan
            # Resolve applicable services list — empty list = applies to all services
            applicable_services = []
            try:
                raw_refs = plan._data.get('applicable_services') or []
                for ref in raw_refs:
                    sid = ref.id if hasattr(ref, 'id') else ref
                    sid_str = str(sid)
                    name = getattr(ref, 'name', None)
                    applicable_services.append({'id': sid_str, 'name': name or 'Service'})
            except Exception:
                applicable_services = []

            membership_data['plan'] = {
                'id': str(plan.id),
                'name': plan.name,
                'allocated_discount': plan.allocated_discount,
                'validity_days': plan.validity_days,
                'description': plan.description,
                'applicable_services': applicable_services,
                'applicable_service_ids': [s['id'] for s in applicable_services],
            }
        
        response = jsonify({
            'active': True,
            'membership': membership_data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Customer.DoesNotExist:
        response = jsonify({'error': 'Customer not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        print(f"Error fetching customer active membership: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_bp.route('/search', methods=['GET'])
@require_auth
def search_customers(current_user=None):
    """Search customers by mobile or name (min 3 chars), scoped to current branch"""
    query = request.args.get('q', '')

    if len(query) < 3:
        return jsonify({'customers': []})

    # Scope to the caller's current branch so one branch cannot enumerate another's directory
    branch = get_selected_branch(request, current_user)
    customer_query = Customer.objects.filter(merged_into=None)
    customer_query = apply_branch_scope(customer_query, branch, current_user)

    customers = customer_query.filter(
        Q(mobile__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(secondary_mobiles=query)
    ).limit(10)
    
    return jsonify({
        'customers': [{
            'id': str(c.id),
            'mobile': c.mobile,
            'firstName': c.first_name,
            'lastName': c.last_name
        } for c in customers]
    })
