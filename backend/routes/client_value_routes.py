from flask import Blueprint, jsonify, request
from models import Customer, Bill
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist
from bson import ObjectId

client_value_bp = Blueprint('client_value', __name__)

def handle_preflight():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@client_value_bp.route('/api/analytics/client-revenue-pareto', methods=['OPTIONS'])
def client_revenue_pareto_preflight():
    return handle_preflight()

@client_value_bp.route('/api/analytics/client-revenue-pareto', methods=['GET'])
def client_revenue_pareto():
    """Get client revenue distribution for Pareto chart (80/20 rule)"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        top_n = int(request.args.get('top_n', 10))

        # Default to last 12 months if no dates provided
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=365)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')

        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # Query bills in date range
        bills = Bill.objects.filter(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lt=end
        )

        # Calculate revenue per client
        client_revenue = {}
        client_visits = {}
        client_last_visit = {}
        
        for bill in bills:
            if not bill.customer:
                continue
            
            try:
                # Ensure customer is loaded
                if hasattr(bill.customer, 'id'):
                    customer_id = str(bill.customer.id)
                else:
                    continue
                    
                # Use final_amount (gross) for revenue
                revenue = float(bill.final_amount or 0)
                
                if customer_id not in client_revenue:
                    client_revenue[customer_id] = 0
                    client_visits[customer_id] = 0
                    client_last_visit[customer_id] = bill.bill_date
                
                client_revenue[customer_id] += revenue
                client_visits[customer_id] += 1
                
                # Compare dates properly
                if isinstance(bill.bill_date, datetime) and isinstance(client_last_visit[customer_id], datetime):
                    if bill.bill_date > client_last_visit[customer_id]:
                        client_last_visit[customer_id] = bill.bill_date
                elif bill.bill_date:
                    client_last_visit[customer_id] = bill.bill_date
            except Exception as e:
                # Skip bills with errors
                print(f"Error processing bill {bill.id}: {str(e)}")
                continue

        # Build client list with details
        clients = []
        for customer_id, revenue in client_revenue.items():
            try:
                customer = Customer.objects.get(id=customer_id)
                full_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
                if not full_name:
                    full_name = f"Customer {customer_id}"
                
                clients.append({
                    'id': customer_id,
                    'name': full_name,
                    'revenue': round(revenue, 2),
                    'visits': client_visits[customer_id],
                    'last_visit': client_last_visit[customer_id].strftime('%Y-%m-%d') if isinstance(client_last_visit[customer_id], datetime) else str(client_last_visit[customer_id])
                })
            except DoesNotExist:
                continue

        # Sort by revenue descending
        clients.sort(key=lambda x: x['revenue'], reverse=True)

        # Calculate total revenue
        total_revenue = sum(c['revenue'] for c in clients)

        if total_revenue == 0:
            response = jsonify({
                'labels': [],
                'spend': [],
                'cumulativePct': [],
                'totalRevenue': 0,
                'clientData': []
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # Get top N clients
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
                'last_visit': client['last_visit'],
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
                'id': 0,
                'name': 'Other Clients',
                'revenue': round(others_revenue, 2),
                'visits': sum(c['visits'] for c in clients[top_n:]),
                'last_visit': 'N/A',
                'cumulative_pct': round(cumulative_percentage, 1),
                'color': '#9ca3af'
            })

        # Calculate VIP metrics
        vip_count = max(1, int(len(clients) * 0.2))
        vip_revenue = sum(c['revenue'] for c in clients[:vip_count])
        vip_percentage = (vip_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        avg_lifetime_value = total_revenue / len(clients) if len(clients) > 0 else 0
        vip_avg = vip_revenue / vip_count if vip_count > 0 else 0
        vip_multiple = vip_avg / avg_lifetime_value if avg_lifetime_value > 0 else 0

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
                'vipSpendMultiple': round(vip_multiple, 1)
            },
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
            'id': client['id'],
            'name': client['name'],
            'initials': get_initials(client['name']),
            'color': get_color_for_index(i),
            'total_visits': client['visits'],
            'last_visit': client['last_visit'],
            'total_spend': client['revenue']
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

