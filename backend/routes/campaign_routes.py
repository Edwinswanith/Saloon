from flask import Blueprint, request, jsonify
from models import Customer, Bill, OfferCampaign, WhatsAppMessage, Branch
from datetime import datetime, timedelta
from bson import ObjectId
from utils.auth import require_auth, require_role
from utils.branch_filter import get_selected_branch
from utils.whatsapp_service import send_whatsapp_message
from models import to_dict

campaign_bp = Blueprint('campaigns', __name__)

@campaign_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

def get_filtered_customers(filter_type, branch):
    """Get customers based on filter type"""
    base_query = Customer.objects(merged_into=None)
    
    if branch:
        base_query = base_query.filter(branch=branch)
    
    if filter_type == 'all':
        customers = list(base_query)
        # Calculate stats for each customer
        result = []
        for customer in customers:
            match_stage = {
                "customer": ObjectId(str(customer.id)),
                "is_deleted": False
            }
            if branch:
                match_stage["branch"] = ObjectId(str(branch.id))
            
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
            total_revenue = bills_result[0].get('total_revenue', 0.0) if bills_result else 0.0
            total_visits = bills_result[0].get('total_visits', 0) if bills_result else 0
            
            result.append({
                'id': str(customer.id),
                'name': f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A',
                'mobile': customer.mobile,
                'total_revenue': total_revenue,
                'total_visits': total_visits,
                'whatsapp_consent': customer.whatsapp_consent or False
            })
        return result
    
    elif filter_type == 'top10_revenue':
        # Get top 10 by revenue
        match_stage = {"is_deleted": False}
        if branch:
            match_stage["branch"] = ObjectId(str(branch.id))
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$customer",
                "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10}
        ]
        
        top_customers = list(Bill.objects.aggregate(pipeline))
        customer_ids = [item['_id'] for item in top_customers if item['_id']]
        
        customers = list(base_query.filter(id__in=customer_ids))
        result = []
        for customer in customers:
            revenue_dict = {str(item['_id']): item['total_revenue'] for item in top_customers}
            result.append({
                'id': str(customer.id),
                'name': f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A',
                'mobile': customer.mobile,
                'total_revenue': revenue_dict.get(str(customer.id), 0.0),
                'total_visits': 0,  # Would need separate aggregation
                'whatsapp_consent': customer.whatsapp_consent or False
            })
        # Sort by revenue descending
        result.sort(key=lambda x: x['total_revenue'], reverse=True)
        return result
    
    elif filter_type == 'top10_visits':
        # Get top 10 by visits
        match_stage = {"is_deleted": False}
        if branch:
            match_stage["branch"] = ObjectId(str(branch.id))
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$customer",
                "total_visits": {"$sum": 1}
            }},
            {"$sort": {"total_visits": -1}},
            {"$limit": 10}
        ]
        
        top_customers = list(Bill.objects.aggregate(pipeline))
        customer_ids = [item['_id'] for item in top_customers if item['_id']]
        
        customers = list(base_query.filter(id__in=customer_ids))
        result = []
        for customer in customers:
            visits_dict = {str(item['_id']): item['total_visits'] for item in top_customers}
            result.append({
                'id': str(customer.id),
                'name': f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A',
                'mobile': customer.mobile,
                'total_revenue': 0.0,  # Would need separate aggregation
                'total_visits': visits_dict.get(str(customer.id), 0),
                'whatsapp_consent': customer.whatsapp_consent or False
            })
        # Sort by visits descending
        result.sort(key=lambda x: x['total_visits'], reverse=True)
        return result
    
    elif filter_type == 'gender_female':
        customers = list(base_query.filter(gender='Female'))
    elif filter_type == 'gender_male':
        customers = list(base_query.filter(gender='Male'))
    elif filter_type == 'inactive':
        # Customers with no visit in last 60 days
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        match_stage = {
            "is_deleted": False,
            "bill_date": {"$lt": cutoff_date}
        }
        if branch:
            match_stage["branch"] = ObjectId(str(branch.id))
        
        # Get customers who have bills but none in last 60 days
        recent_bills = Bill.objects(**match_stage).distinct('customer')
        all_customers_with_bills = Bill.objects(is_deleted=False).distinct('customer')
        if branch:
            all_customers_with_bills = Bill.objects(is_deleted=False, branch=branch).distinct('customer')
        
        inactive_customer_ids = [c for c in all_customers_with_bills if c not in recent_bills]
        customers = list(base_query.filter(id__in=inactive_customer_ids))
    else:
        customers = list(base_query)
    
    # For non-top10 filters, calculate stats
    result = []
    for customer in customers:
        match_stage = {
            "customer": ObjectId(str(customer.id)),
            "is_deleted": False
        }
        if branch:
            match_stage["branch"] = ObjectId(str(branch.id))
        
        bills_pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}},
                "total_visits": {"$sum": 1}
            }}
        ]
        
        bills_result = list(Bill.objects.aggregate(bills_pipeline))
        total_revenue = bills_result[0].get('total_revenue', 0.0) if bills_result else 0.0
        total_visits = bills_result[0].get('total_visits', 0) if bills_result else 0
        
        result.append({
            'id': str(customer.id),
            'name': f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A',
            'mobile': customer.mobile,
            'total_revenue': total_revenue,
            'total_visits': total_visits,
            'whatsapp_consent': customer.whatsapp_consent or False
        })
    
    return result

@campaign_bp.route('/customers', methods=['GET'])
@require_role('manager', 'owner')
def get_campaign_customers(current_user=None):
    """Get filtered customer list for campaign targeting"""
    try:
        filter_type = request.args.get('filter', 'all')
        branch = get_selected_branch(request, current_user)
        
        if not branch:
            response = jsonify({'error': 'Branch selection required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        customers = get_filtered_customers(filter_type, branch)
        
        response = jsonify({
            'customers': customers,
            'count': len(customers),
            'filter_type': filter_type
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error fetching campaign customers: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@campaign_bp.route('/birthday-customers', methods=['GET'])
@require_role('manager', 'owner')
def get_birthday_customers(current_user=None):
    """Get customers whose birthday falls in the specified month"""
    try:
        month = request.args.get('month', type=int)
        if not month or month < 1 or month > 12:
            response = jsonify({'error': 'Valid month (1-12) is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch selection required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Use aggregation pipeline since MongoEngine doesn't support __month on date fields
        match_stage = {
            "merged_into": None,
            "dob": {"$exists": True, "$ne": None}
        }
        if branch:
            match_stage["branch"] = ObjectId(str(branch.id))

        pipeline = [
            {"$match": match_stage},
            {"$addFields": {"dob_month": {"$month": "$dob"}}},
            {"$match": {"dob_month": month}}
        ]

        customer_docs = list(Customer.objects.aggregate(pipeline))
        customer_ids = [doc['_id'] for doc in customer_docs]
        customers = list(Customer.objects(id__in=customer_ids))
        
        result = []
        for customer in customers:
            customer_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A'
            result.append({
                'id': str(customer.id),
                'name': customer_name,
                'mobile': customer.mobile,
                'dob': customer.dob.isoformat() if customer.dob else None,
                'whatsapp_consent': customer.whatsapp_consent or False
            })
        
        # Sort by day of month
        result.sort(key=lambda x: int(x['dob'].split('-')[2]) if x['dob'] else 999)
        
        response = jsonify({
            'customers': result,
            'count': len(result),
            'month': month
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error fetching birthday customers: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@campaign_bp.route('/send', methods=['POST'])
@require_role('manager', 'owner')
def send_campaign(current_user=None):
    """Send offer campaign to selected customers"""
    try:
        data = request.json
        
        if not data.get('message_text'):
            response = jsonify({'error': 'Message text is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch selection required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        filter_type = data.get('filter_type', 'all')
        customer_ids = data.get('customer_ids', [])  # Optional: specific customer IDs
        
        # Get customers to send to
        if customer_ids:
            # Send to specific customers
            customers = list(Customer.objects(id__in=customer_ids, branch=branch, merged_into=None))
        else:
            # Use filter
            customers_data = get_filtered_customers(filter_type, branch)
            customer_ids = [c['id'] for c in customers_data]
            customers = list(Customer.objects(id__in=customer_ids, branch=branch, merged_into=None))
        
        if not customers:
            response = jsonify({'error': 'No customers found to send campaign to'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Create campaign record
        created_by_name = current_user.get('name', 'Unknown') if current_user else 'Unknown'
        campaign_type = data.get('campaign_type', 'general')
        campaign = OfferCampaign(
            name=data.get('name', ''),
            message_text=data['message_text'],
            image_data=data.get('image_data'),
            image_mime_type=data.get('image_mime_type'),
            filter_type=filter_type,
            campaign_type=campaign_type,
            branch=branch,
            status='pending',
            created_by_name=created_by_name
        )
        campaign.save()
        
        # Send messages
        sent_count = 0
        failed_count = 0
        
        for customer in customers:
            try:
                # Only send to customers with WhatsApp consent
                if not customer.whatsapp_consent:
                    failed_count += 1
                    continue
                
                result = send_whatsapp_message(
                    customer=customer,
                    message_text=data['message_text'],
                    image_data=data.get('image_data'),
                    image_mime_type=data.get('image_mime_type')
                )
                
                # Save WhatsApp message record
                whatsapp_msg = WhatsAppMessage(
                    customer=customer,
                    branch=branch,
                    message_text=data['message_text'],
                    delivery_status=result.get('delivery_status', 'pending'),
                    sent_at=datetime.utcnow()
                )
                whatsapp_msg.save()
                
                if result.get('success'):
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error sending to customer {customer.id}: {str(e)}")
                failed_count += 1
        
        # Update campaign status
        campaign.sent_count = sent_count
        campaign.failed_count = failed_count
        campaign.status = 'completed' if sent_count > 0 else 'failed'
        campaign.save()
        
        response = jsonify({
            'campaign_id': str(campaign.id),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'message': f'Campaign sent to {sent_count} customers'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error sending campaign: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@campaign_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_campaigns(current_user=None):
    """Get campaign history"""
    try:
        branch = get_selected_branch(request, current_user)
        campaign_type = request.args.get('type')  # Optional filter: 'general' or 'birthday'
        
        query = OfferCampaign.objects()
        if branch:
            query = query.filter(branch=branch)
        if campaign_type:
            query = query.filter(campaign_type=campaign_type)
        
        campaigns = list(query.order_by('-created_at').limit(50))
        
        result = []
        for campaign in campaigns:
            result.append({
                'id': str(campaign.id),
                'name': campaign.name or 'Untitled Campaign',
                'message_text': campaign.message_text[:100] + '...' if len(campaign.message_text) > 100 else campaign.message_text,
                'filter_type': campaign.filter_type,
                'campaign_type': getattr(campaign, 'campaign_type', 'general'),
                'sent_count': campaign.sent_count,
                'failed_count': campaign.failed_count,
                'status': campaign.status,
                'created_by_name': campaign.created_by_name,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'has_image': bool(campaign.image_data)
            })
        
        response = jsonify({
            'campaigns': result,
            'count': len(result)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        print(f"Error fetching campaigns: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

