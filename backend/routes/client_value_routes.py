from flask import Blueprint, jsonify, request
from models import Customer, Bill, Membership, Branch
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.date_utils import get_ist_date_range
from utils.auth import require_auth

client_value_bp = Blueprint('client_value', __name__)

def handle_preflight():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Branch-Id')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@client_value_bp.route('/api/analytics/client-revenue-pareto', methods=['OPTIONS'])
def client_revenue_pareto_preflight():
    return handle_preflight()

@client_value_bp.route('/api/analytics/client-revenue-pareto', methods=['GET'])
@require_auth
def client_revenue_pareto(current_user=None):
    """Get client revenue distribution for Pareto chart (80/20 rule) with MongoDB aggregations"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        top_n = int(request.args.get('top_n', 10))
        membership_filter = request.args.get('membership', 'all')  # all, with, without

        # Get branch filter
        branch = get_selected_branch(request, current_user)
        branch_id = str(branch.id) if branch else None

        # Default to last 12 months if no dates provided
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=365)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')

        # Convert IST dates to UTC using date_utils
        start_utc, end_utc = get_ist_date_range(start_date, end_date)

        # Build aggregation pipeline
        pipeline = []

        # Stage 1: Match bills in date range, not deleted, with customer
        match_stage = {
            'is_deleted': False,
            'bill_date': {'$gte': start_utc, '$lte': end_utc},
            'customer': {'$exists': True, '$ne': None}
        }
        
        # Add branch filter if specified
        if branch_id and ObjectId.is_valid(branch_id):
            match_stage['branch'] = ObjectId(branch_id)
        
        pipeline.append({'$match': match_stage})

        # Stage 2: Group by customer, calculate totals
        pipeline.append({
            '$group': {
                '_id': '$customer',
                'totalSpend': {'$sum': '$final_amount'},
                'visitCount': {'$sum': 1},
                'lastVisit': {'$max': '$bill_date'},
                'branch': {'$first': '$branch'}  # Get branch from most recent bill
            }
        })

        # Stage 3: Lookup customer details
        pipeline.append({
            '$lookup': {
                'from': 'customers',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'customerDetails'
            }
        })

        pipeline.append({
            '$unwind': {
                'path': '$customerDetails',
                'preserveNullAndEmptyArrays': True
            }
        })

        # Stage 4: Calculate average bill value
        pipeline.append({
            '$addFields': {
                'avgBillValue': {
                    '$cond': {
                        'if': {'$gt': ['$visitCount', 0]},
                        'then': {'$divide': ['$totalSpend', '$visitCount']},
                        'else': 0
                    }
                },
                'customerName': {
                    '$concat': [
                        {'$ifNull': ['$customerDetails.first_name', '']},
                        ' ',
                        {'$ifNull': ['$customerDetails.last_name', '']}
                    ]
                },
                'customerBranch': '$customerDetails.branch'
            }
        })

        # Stage 5: Lookup membership status
        pipeline.append({
            '$lookup': {
                'from': 'memberships',
                'let': {'customerId': '$_id'},
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$eq': ['$customer', '$$customerId']},
                                    {'$eq': ['$status', 'active']},
                                    {'$gt': ['$expiry_date', datetime.utcnow()]}
                                ]
                            }
                        }
                    }
                ],
                'as': 'activeMemberships'
            }
        })

        pipeline.append({
            '$addFields': {
                'hasActiveMembership': {
                    '$gt': [{'$size': '$activeMemberships'}, 0]
                },
                'membershipStatus': {
                    '$cond': {
                        'if': {'$gt': [{'$size': '$activeMemberships'}, 0]},
                        'then': 'active',
                        'else': 'none'
                    }
                }
            }
        })

        # Stage 6: Filter by membership status if specified
        if membership_filter == 'with':
            pipeline.append({'$match': {'hasActiveMembership': True}})
        elif membership_filter == 'without':
            pipeline.append({'$match': {'hasActiveMembership': False}})

        # Stage 7: Lookup branch name
        pipeline.append({
            '$lookup': {
                'from': 'branches',
                'localField': 'customerBranch',
                'foreignField': '_id',
                'as': 'branchDetails'
            }
        })

        pipeline.append({
            '$addFields': {
                'branchName': {
                    '$ifNull': [
                        {'$arrayElemAt': ['$branchDetails.name', 0]},
                        'Unknown'
                    ]
                },
                'branchId': {
                    '$ifNull': [
                        {'$arrayElemAt': ['$branchDetails._id', 0]},
                        None
                    ]
                }
            }
        })

        # Stage 8: Project final fields
        pipeline.append({
            '$project': {
                'customerId': {'$toString': '$_id'},
                'name': {
                    '$cond': {
                        'if': {'$ne': ['$customerName', ' ']},
                        'then': {'$trim': {'input': '$customerName'}},
                        'else': {'$concat': ['Customer ', {'$toString': '$_id'}]}
                    }
                },
                'totalSpend': 1,
                'visitCount': 1,
                'avgBillValue': 1,
                'lastVisit': 1,
                'membershipStatus': 1,
                'hasActiveMembership': 1,
                'branch': {
                    'id': {'$ifNull': [{'$toString': '$branchId'}, None]},
                    'name': '$branchName'
                }
            }
        })

        # Execute aggregation
        clients_raw = list(Bill.objects.aggregate(pipeline))
        
        # Convert to list of dicts
        clients = []
        for client in clients_raw:
            clients.append({
                'id': client.get('customerId', ''),
                'name': client.get('name', 'Unknown'),
                'revenue': round(float(client.get('totalSpend', 0)), 2),
                'visits': int(client.get('visitCount', 0)),
                'avgBillValue': round(float(client.get('avgBillValue', 0)), 2),
                'last_visit': client.get('lastVisit').strftime('%Y-%m-%d') if client.get('lastVisit') else None,
                'membershipStatus': client.get('membershipStatus', 'none'),
                'branch': client.get('branch', {})
            })

        # Sort by revenue descending
        clients.sort(key=lambda x: x['revenue'], reverse=True)

        # Calculate total revenue and averages
        total_revenue = sum(c['revenue'] for c in clients)
        total_customers = len(clients)
        avg_lifetime_value = total_revenue / total_customers if total_customers > 0 else 0
        avg_visit_frequency = sum(c['visits'] for c in clients) / total_customers if total_customers > 0 else 0
        avg_bill_value = sum(c['avgBillValue'] for c in clients) / total_customers if total_customers > 0 else 0

        # Calculate VIP status (top 20% by spend AND above average visit frequency)
        if total_customers > 0:
            vip_threshold_index = max(1, int(total_customers * 0.2))
            vip_spend_threshold = clients[vip_threshold_index - 1]['revenue'] if vip_threshold_index <= len(clients) else 0
            
            for client in clients:
                is_top_20_spender = client['revenue'] >= vip_spend_threshold
                is_above_avg_visits = client['visits'] > avg_visit_frequency
                client['isVIP'] = is_top_20_spender and is_above_avg_visits
                
                # Build VIP reasons
                vip_reasons = []
                if is_top_20_spender:
                    vip_reasons.append('Top 20% spender')
                if is_above_avg_visits:
                    vip_reasons.append('Above average visit frequency')
                if client['membershipStatus'] == 'active':
                    vip_reasons.append('Active membership holder')
                client['vipReasons'] = vip_reasons
        else:
            for client in clients:
                client['isVIP'] = False
                client['vipReasons'] = []

        # Calculate VIP metrics
        vip_customers = [c for c in clients if c.get('isVIP', False)]
        vip_count = len(vip_customers)
        vip_revenue = sum(c['revenue'] for c in vip_customers)
        vip_percentage = (vip_revenue / total_revenue * 100) if total_revenue > 0 else 0
        vip_avg = vip_revenue / vip_count if vip_count > 0 else 0
        vip_multiple = vip_avg / avg_lifetime_value if avg_lifetime_value > 0 else 0

        # Count active memberships
        active_memberships_count = len([c for c in clients if c.get('membershipStatus') == 'active'])

        if total_revenue == 0:
            response = jsonify({
                'labels': [],
                'spend': [],
                'cumulativePct': [],
                'totalRevenue': 0,
                'clientData': [],
                'metrics': {
                    'totalVIPClients': 0,
                    'percentageRevenueFromVIPs': 0,
                    'avgLifetimeValue': 0,
                    'vipSpendMultiple': 0,
                    'avgBillValue': 0,
                    'avgVisitFrequency': 0,
                    'activeMemberships': 0
                },
                'customers': [],
                'topSpenders': [],
                'mostFrequent': [],
                'newHighValue': []
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # Get top N clients for chart
        top_clients = clients[:top_n]
        
        # Calculate "Other Clients" bucket
        others_revenue = sum(c['revenue'] for c in clients[top_n:])
        others_count = len(clients) - top_n

        # Build labels, spend, and cumulative percentage arrays
        labels = []
        spend = []
        cumulative_pct = []
        cumulative_revenue = 0
        client_data = []

        # Add top clients
        for i, client in enumerate(top_clients):
            cumulative_revenue += client['revenue']
            cumulative_percentage = (cumulative_revenue / total_revenue) * 100
            
            labels.append(client['name'])
            spend.append(client['revenue'])
            cumulative_pct.append(round(cumulative_percentage, 1))
            
            client_data.append({
                'id': client['id'],
                'name': client['name'],
                'revenue': client['revenue'],
                'visits': client['visits'],
                'avgBillValue': client['avgBillValue'],
                'last_visit': client['last_visit'],
                'membershipStatus': client['membershipStatus'],
                'branch': client['branch'],
                'isVIP': client.get('isVIP', False),
                'cumulative_pct': round(cumulative_percentage, 1),
                'color': get_color_for_index(i)
            })

        # Add "Other Clients" bucket if there are more clients
        if others_count > 0:
            cumulative_revenue += others_revenue
            cumulative_percentage = (cumulative_revenue / total_revenue) * 100
            
            labels.append('Other Clients')
            spend.append(round(others_revenue, 2))
            cumulative_pct.append(round(cumulative_percentage, 1))
            
            client_data.append({
                'id': '0',
                'name': 'Other Clients',
                'revenue': round(others_revenue, 2),
                'visits': sum(c['visits'] for c in clients[top_n:]),
                'avgBillValue': 0,
                'last_visit': None,
                'membershipStatus': 'none',
                'branch': {},
                'isVIP': False,
                'cumulative_pct': round(cumulative_percentage, 1),
                'color': '#9ca3af'
            })

        # Prepare response
        response_data = {
            'labels': labels,
            'spend': spend,
            'cumulativePct': cumulative_pct,
            'totalRevenue': round(total_revenue, 2),
            'clientData': client_data,
            'metrics': {
                'totalVIPClients': vip_count,
                'percentageRevenueFromVIPs': round(vip_percentage, 1),
                'avgLifetimeValue': round(avg_lifetime_value, 2),
                'vipSpendMultiple': round(vip_multiple, 1),
                'avgBillValue': round(avg_bill_value, 2),
                'avgVisitFrequency': round(avg_visit_frequency, 2),
                'activeMemberships': active_memberships_count
            },
            'customers': clients,
            'topSpenders': build_client_list(clients[:20]),
            'mostFrequent': build_client_list(sorted(clients, key=lambda x: x['visits'], reverse=True)[:20]),
            'newHighValue': get_new_high_value_clients(clients, avg_lifetime_value)
        }

        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"Error in client_revenue_pareto: {str(e)}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

def build_client_list(clients):
    """Build formatted client list for tables"""
    result = []
    for i, client in enumerate(clients):
        result.append({
            'id': client.get('id', ''),
            'name': client.get('name', 'Unknown'),
            'initials': get_initials(client.get('name', '')),
            'color': get_color_for_index(i),
            'total_visits': client.get('visits', 0),
            'last_visit': client.get('last_visit'),
            'total_spend': client.get('revenue', 0),
            'avgBillValue': client.get('avgBillValue', 0),
            'membershipStatus': client.get('membershipStatus', 'none'),
            'branch': client.get('branch', {}),
            'isVIP': client.get('isVIP', False),
            'vipReasons': client.get('vipReasons', [])
        })
    return result

def get_new_high_value_clients(all_clients, avg_value):
    """Get clients who joined recently and spend above average"""
    six_months_ago = datetime.now() - timedelta(days=180)
    new_high_value = []
    
    for client in all_clients:
        try:
            customer = Customer.objects.get(id=client['id'])
            if customer and customer.created_at and customer.created_at >= six_months_ago:
                if client['revenue'] > avg_value:
                    new_high_value.append(client)
        except DoesNotExist:
            continue
    
    new_high_value.sort(key=lambda x: x['revenue'], reverse=True)
    return build_client_list(new_high_value[:20])

def get_initials(name):
    """Get initials from a name"""
    if not name or name == 'Other Clients':
        return 'O'
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def get_color_for_index(index):
    """Get a color for a given index"""
    colors = [
        '#ef4444', '#8b5cf6', '#10b981', '#f59e0b', '#3b82f6',
        '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#9ca3af',
        '#f43f5e', '#a855f7', '#22c55e', '#eab308', '#0ea5e9'
    ]
    return colors[index % len(colors)]

@client_value_bp.route('/api/analytics/customer-details/<customer_id>', methods=['OPTIONS'])
def customer_details_preflight(customer_id):
    return handle_preflight()

@client_value_bp.route('/api/analytics/customer-details/<customer_id>', methods=['GET'])
@require_auth
def customer_details(customer_id, current_user=None):
    """Get detailed customer information for popup view"""
    try:
        # Get customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except DoesNotExist:
            response = jsonify({'error': 'Customer not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # Get branch filter
        branch = get_selected_branch(request, current_user)
        branch_id = str(branch.id) if branch else None

        # Build customer name
        full_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
        if not full_name:
            full_name = f"Customer {customer_id}"

        # Get customer bills
        bills_query = Bill.objects.filter(
            customer=customer,
            is_deleted=False
        )
        
        if branch_id:
            bills_query = bills_query.filter(branch=ObjectId(branch_id))
        
        bills = list(bills_query.order_by('-bill_date').limit(10))
        
        # Calculate totals
        total_spend = sum(float(bill.final_amount or 0) for bill in bills_query)
        visit_count = bills_query.count()
        avg_bill_value = total_spend / visit_count if visit_count > 0 else 0
        last_visit = bills[0].bill_date if bills else None

        # Get membership status
        membership_query = Membership.objects.filter(
            customer=customer,
            status='active',
            expiry_date__gt=datetime.utcnow()
        )
        if branch_id:
            membership_query = membership_query.filter(branch=ObjectId(branch_id))
        
        active_membership = membership_query.first()
        membership_status = 'active' if active_membership else 'none'
        membership_details = None
        if active_membership:
            membership_details = {
                'name': active_membership.name,
                'purchaseDate': active_membership.purchase_date.isoformat() if active_membership.purchase_date else None,
                'expiryDate': active_membership.expiry_date.isoformat() if active_membership.expiry_date else None,
                'price': float(active_membership.price or 0)
            }

        # Get branch info
        branch_info = None
        if customer.branch:
            branch_info = {
                'id': str(customer.branch.id),
                'name': customer.branch.name
            }
        elif bills and bills[0].branch:
            branch_info = {
                'id': str(bills[0].branch.id),
                'name': bills[0].branch.name
            }

        # Get service preferences (most booked services)
        service_counts = {}
        for bill in bills_query:
            if bill.items:
                for item in bill.items:
                    if item.item_type == 'service' and item.service:
                        service_id = str(item.service.id)
                        if service_id not in service_counts:
                            try:
                                service = item.service
                                service_name = service.name if hasattr(service, 'name') else 'Unknown Service'
                                service_counts[service_id] = {'name': service_name, 'count': 0}
                            except:
                                continue
                        service_counts[service_id]['count'] += item.quantity if item.quantity else 1
        
        service_preferences = sorted(
            service_counts.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:5]

        # Get staff preferences (most frequent staff)
        staff_counts = {}
        for bill in bills_query:
            if bill.items:
                for item in bill.items:
                    if item.staff:
                        try:
                            staff_id = str(item.staff.id) if hasattr(item.staff, 'id') else str(item.staff)
                            if staff_id not in staff_counts:
                                staff = item.staff
                                if hasattr(staff, 'first_name'):
                                    staff_name = f"{staff.first_name or ''} {staff.last_name or ''}".strip()
                                    if not staff_name:
                                        staff_name = 'Unknown Staff'
                                else:
                                    staff_name = 'Unknown Staff'
                                staff_counts[staff_id] = {'name': staff_name, 'count': 0}
                            staff_counts[staff_id]['count'] += 1
                        except:
                            continue
        
        staff_preferences = sorted(
            staff_counts.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:3]

        # Build recent activity (last 10 bills)
        recent_activity = []
        for bill in bills[:10]:
            bill_items = []
            if bill.items:
                for item in bill.items:
                    item_name = 'Unknown'
                    if item.item_type == 'service' and item.service:
                        try:
                            item_name = item.service.name if hasattr(item.service, 'name') else 'Service'
                        except:
                            item_name = 'Service'
                    elif item.item_type == 'package' and item.package:
                        try:
                            item_name = item.package.name if hasattr(item.package, 'name') else 'Package'
                        except:
                            item_name = 'Package'
                    elif item.item_type == 'product' and item.product:
                        try:
                            item_name = item.product.name if hasattr(item.product, 'name') else 'Product'
                        except:
                            item_name = 'Product'
                    bill_items.append(item_name)
            
            recent_activity.append({
                'date': bill.bill_date.isoformat() if bill.bill_date else None,
                'amount': float(bill.final_amount or 0),
                'services': bill_items[:5]  # Limit to 5 services for display
            })

        # Calculate VIP status and reasons
        # Get all customers for comparison
        all_customers_query = Bill.objects.filter(is_deleted=False)
        if branch_id:
            all_customers_query = all_customers_query.filter(branch=ObjectId(branch_id))
        
        all_customer_stats = {}
        for bill in all_customers_query:
            if bill.customer:
                cust_id = str(bill.customer.id)
                if cust_id not in all_customer_stats:
                    all_customer_stats[cust_id] = {'spend': 0, 'visits': 0}
                all_customer_stats[cust_id]['spend'] += float(bill.final_amount or 0)
                all_customer_stats[cust_id]['visits'] += 1
        
        if all_customer_stats:
            all_spends = sorted([s['spend'] for s in all_customer_stats.values()], reverse=True)
            all_visits = [s['visits'] for s in all_customer_stats.values()]
            
            avg_spend = sum(all_spends) / len(all_spends) if all_spends else 0
            avg_visits = sum(all_visits) / len(all_visits) if all_visits else 0
            
            customer_spend = all_customer_stats.get(customer_id, {}).get('spend', 0)
            customer_visits = all_customer_stats.get(customer_id, {}).get('visits', 0)
            
            vip_threshold_index = max(1, int(len(all_spends) * 0.2))
            vip_spend_threshold = all_spends[vip_threshold_index - 1] if vip_threshold_index <= len(all_spends) else 0
            
            is_top_20_spender = customer_spend >= vip_spend_threshold
            is_above_avg_visits = customer_visits > avg_visits
            is_vip = is_top_20_spender and is_above_avg_visits
            
            vip_reasons = []
            if is_top_20_spender:
                vip_reasons.append('Top 20% spender')
            if is_above_avg_visits:
                vip_reasons.append('Above average visit frequency')
            if membership_status == 'active':
                vip_reasons.append('Active membership holder')
            if customer.created_at:
                days_since_join = (datetime.utcnow() - customer.created_at).days
                if days_since_join > 180:
                    vip_reasons.append(f'Consistent customer since {customer.created_at.strftime("%Y-%m-%d")}')
        else:
            is_vip = False
            vip_reasons = []

        # Build response
        response_data = {
            'customer': {
                'id': customer_id,
                'name': full_name,
                'mobile': customer.mobile or '',
                'email': customer.email or '',
                'branch': branch_info
            },
            'metrics': {
                'totalSpend': round(total_spend, 2),
                'visitCount': visit_count,
                'avgBillValue': round(avg_bill_value, 2),
                'lastVisit': last_visit.isoformat() if last_visit else None,
                'membershipStatus': membership_status
            },
            'membership': membership_details,
            'isVIP': is_vip,
            'vipReasons': vip_reasons,
            'recentActivity': recent_activity,
            'servicePreferences': service_preferences,
            'staffPreferences': staff_preferences
        }

        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"Error in customer_details: {str(e)}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

