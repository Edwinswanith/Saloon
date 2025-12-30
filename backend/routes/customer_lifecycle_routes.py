from flask import Blueprint, request, jsonify
from mongoengine import Q
from datetime import datetime, timedelta
from models import Customer, Bill, WhatsAppTemplate, WhatsAppMessage, Staff
from utils.auth import require_auth, require_role, get_current_user
from utils.whatsapp_service import send_whatsapp_message
from utils.branch_filter import get_selected_branch, filter_by_branch
from models import to_dict

customer_lifecycle_bp = Blueprint('customer_lifecycle', __name__)

def calculate_customer_segment(customer):
    """Calculate customer segment based on visit history"""
    # Handle None values with defaults
    total_visits = customer.total_visits if customer.total_visits is not None else 0
    total_spent = customer.total_spent if customer.total_spent is not None else 0.0
    
    if total_visits == 0:
        return 'new'
    elif total_visits >= 10 and total_spent >= 5000:
        return 'loyal'
    elif total_visits >= 5:
        return 'regular'
    elif total_spent >= 3000:
        return 'high_spending'
    else:
        # Check if inactive (no visit in last 90 days)
        if customer.last_visit_date:
            days_since_visit = (datetime.utcnow().date() - customer.last_visit_date).days
            if days_since_visit > 90:
                return 'inactive'
        return 'regular'

@customer_lifecycle_bp.route('/report', methods=['GET'])
@require_role('manager', 'owner')
def get_lifecycle_report(current_user=None):
    """Get segmented customer list with filters"""
    try:
        segment = request.args.get('segment')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_spent = request.args.get('min_spent', type=float)
        min_visits = request.args.get('min_visits', type=int)
        
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Debug logging
        print(f"\n[Customer Lifecycle Report] === REQUEST START ===")
        print(f"[Customer Lifecycle Report] X-Branch-Id header: {request.headers.get('X-Branch-Id')}")
        print(f"[Customer Lifecycle Report] Selected branch: {branch.name if branch else 'NONE'} (ID: {branch.id if branch else 'NONE'})")
        print(f"[Customer Lifecycle Report] User: {current_user.get('username') if isinstance(current_user, dict) else current_user.username if hasattr(current_user, 'username') else 'UNKNOWN'}")
        print(f"[Customer Lifecycle Report] User role: {current_user.get('role') if isinstance(current_user, dict) else current_user.role if hasattr(current_user, 'role') else 'UNKNOWN'}")
        
        # Validate branch exists
        if not branch:
            response = jsonify({'error': 'Branch not found or not accessible', 'customers': [], 'count': 0})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # CRITICAL FIX: Use __raw__ MongoDB query for reliable filtering
        # MongoEngine ReferenceField filtering is unreliable, use raw MongoDB query
        if not branch:
            print(f"[Customer Lifecycle] ERROR: No branch provided!")
            response = jsonify({'error': 'Branch not found', 'customers': [], 'count': 0})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Get branch ID as ObjectId
        from bson import ObjectId
        branch_id_str = str(branch.id)
        branch_oid = ObjectId(branch_id_str)
        
        print(f"[Customer Lifecycle] Filtering by branch: {branch.name}")
        print(f"[Customer Lifecycle] Branch ID (string): {branch_id_str}")
        print(f"[Customer Lifecycle] Branch ID (ObjectId): {branch_oid}")
        
        # Use __raw__ MongoDB query - this is the MOST reliable method for ReferenceField
        customers = Customer.objects(__raw__={'branch': branch_oid})
        
        # Apply additional filters
        if min_spent:
            customers = customers.filter(total_spent__gte=min_spent)
        if min_visits:
            customers = customers.filter(total_visits__gte=min_visits)
        
        # Exclude null branch customers (shouldn't be needed but safety)
        customers = customers.filter(branch__ne=None)
        
        customer_count = customers.count()
        print(f"[Customer Lifecycle] Query filters: branch={branch_id_str}, min_spent={min_spent}, min_visits={min_visits}")
        print(f"[Customer Lifecycle] Total customers matching query: {customer_count}")
        
        # Verify the filter worked - should be around 85-87 per branch
        if customer_count > 100 or customer_count == 0:
            print(f"[Customer Lifecycle] WARNING: Unexpected customer count ({customer_count}). Expected 85-87.")
            # Log first few customer IDs for debugging
            sample_customers = list(customers.limit(3))
            if sample_customers:
                print(f"[Customer Lifecycle] Sample customers:")
                for c in sample_customers:
                    c_branch_id = str(c.branch.id) if c.branch else 'None'
                    print(f"  - {c.first_name} {c.last_name} (Branch ID: {c_branch_id})")
        else:
            print(f"[Customer Lifecycle] SUCCESS: Correct number of customers returned for branch!")
        
        # Additional validation: Ensure all returned customers belong to the selected branch
        branch_id_str = str(branch.id)
        
        # Ensure all customers have default values for None fields
        for customer in customers:
            needs_update = False
            if customer.total_visits is None:
                customer.total_visits = 0
                needs_update = True
            if customer.total_spent is None:
                customer.total_spent = 0.0
                needs_update = True
            if needs_update:
                customer.save()
        
        result = []
        validation_errors = 0
        for customer in customers:
            # Additional validation: Double-check customer belongs to selected branch
            if customer.branch:
                customer_branch_id = str(customer.branch.id) if hasattr(customer.branch, 'id') else str(customer.branch)
                if customer_branch_id != branch_id_str:
                    # Skip customers that don't match the selected branch (shouldn't happen, but safety check)
                    print(f"[Customer Lifecycle] WARNING: Customer {customer.id} branch mismatch. Expected {branch_id_str}, got {customer_branch_id}")
                    validation_errors += 1
                    continue
            else:
                # Skip customers with no branch (shouldn't happen)
                print(f"[Customer Lifecycle] WARNING: Customer {customer.id} has no branch!")
                validation_errors += 1
                continue
            
            customer_segment = calculate_customer_segment(customer)
            
            # Apply segment filter if specified
            if segment and customer_segment != segment:
                continue
            
            data = to_dict(customer)
            data['segment'] = customer_segment
            # Include branch ID in response for frontend validation
            if customer.branch:
                data['branch_id'] = str(customer.branch.id) if hasattr(customer.branch, 'id') else str(customer.branch)
                data['branch_name'] = customer.branch.name if hasattr(customer.branch, 'name') else 'Unknown'
            result.append(data)
        
        # Debug logging
        print(f"[Customer Lifecycle] Found {len(result)} customers for branch {branch.name} (ID: {branch_id_str})")
        print(f"[Customer Lifecycle] Total customers queried: {customers.count()}")
        print(f"[Customer Lifecycle] Validation errors (branch mismatch): {validation_errors}")
        if segment:
            print(f"[Customer Lifecycle] Filtered by segment: {segment}")
        if result:
            print(f"[Customer Lifecycle] Sample customers: {[(c.get('first_name', 'N/A'), c.get('last_name', 'N/A'), c.get('branch_name', 'N/A')) for c in result[:3]]}")
        print(f"[Customer Lifecycle Report] === REQUEST END ===\n")
        
        response = jsonify({'customers': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_lifecycle_bp.route('/send-whatsapp', methods=['POST'])
@require_role('manager', 'owner')
def send_whatsapp_to_customers(current_user=None):
    """Send WhatsApp message to selected customers"""
    try:
        data = request.json
        customer_ids = data.get('customer_ids', [])
        message_text = data.get('message_text')
        template_id = data.get('template_id')
        segment = data.get('segment')
        
        if not message_text and not template_id:
            response = jsonify({'error': 'Message text or template ID required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        template = None
        if template_id:
            template = WhatsAppTemplate.objects(id=template_id, status='active').first()
            if not template:
                response = jsonify({'error': 'Template not found or inactive'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            message_text = template.message_text
        
        # Get branch for filtering
        branch = get_selected_branch(current_user)
        
        # Get customers
        if customer_ids:
            customers = filter_by_branch(Customer.objects(id__in=customer_ids, whatsapp_consent=True), branch)
        elif segment:
            # Get all customers and filter by segment
            all_customers = filter_by_branch(Customer.objects(whatsapp_consent=True), branch)
            customers = [c for c in all_customers if calculate_customer_segment(c) == segment]
        else:
            response = jsonify({'error': 'Customer IDs or segment required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Get current user (staff/manager)
        sent_by = None
        if current_user and current_user.get('user_type') == 'staff':
            sent_by = Staff.objects(id=current_user['id']).first()
        
        sent_count = 0
        failed_count = 0
        messages = []
        
        for customer in customers:
            result = send_whatsapp_message(customer, message_text, template)
            
            # Create message record
            message = WhatsAppMessage(
                customer=customer,
                template=template,
                message_text=message_text,
                segment=segment or calculate_customer_segment(customer),
                delivery_status=result.get('delivery_status', 'pending'),
                sent_by=sent_by
            )
            message.save()
            messages.append(to_dict(message))
            
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1
        
        response = jsonify({
            'sent': sent_count,
            'failed': failed_count,
            'total': len(customers),
            'messages': messages
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_lifecycle_bp.route('/segments', methods=['GET'])
@require_role('manager', 'owner')
def get_segment_counts(current_user=None):
    """Get customer counts by segment"""
    try:
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Debug logging
        print(f"\n[Customer Segments] === REQUEST START ===")
        print(f"[Customer Segments] X-Branch-Id header: {request.headers.get('X-Branch-Id')}")
        print(f"[Customer Segments] Selected branch: {branch.name if branch else 'NONE'} (ID: {branch.id if branch else 'NONE'})")
        
        # Validate branch exists
        if not branch:
            response = jsonify({'error': 'Branch not found or not accessible', 'segments': {}})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Get customers filtered by branch (using pre-calculated stats)
        # CRITICAL: Use __raw__ MongoDB query for reliable filtering
        from bson import ObjectId
        branch_id_str = str(branch.id)
        branch_oid = ObjectId(branch_id_str)
        
        # Use __raw__ MongoDB query - this is the MOST reliable method for ReferenceField
        customers = Customer.objects(__raw__={'branch': branch_oid}).filter(branch__ne=None)
        
        customer_count = customers.count()
        print(f"[Customer Segments] Filtering by branch: {branch.name} (ID: {branch_id_str})")
        print(f"[Customer Segments] Total customers matching query: {customer_count}")
        
        # Verify the filter worked - should be around 85-87 per branch
        if customer_count > 100 or customer_count == 0:
            print(f"[Customer Segments] WARNING: Unexpected customer count ({customer_count}). Expected 85-87.")
        
        # Ensure all customers have default values for None fields
        customers_updated = 0
        for customer in customers:
            needs_update = False
            if customer.total_visits is None:
                customer.total_visits = 0
                needs_update = True
            if customer.total_spent is None:
                customer.total_spent = 0.0
                needs_update = True
            if needs_update:
                customer.save()
                customers_updated += 1
        
        if customers_updated > 0:
            print(f"Updated {customers_updated} customers with default values")
        
        segments = {
            'new': 0,
            'regular': 0,
            'loyal': 0,
            'inactive': 0,
            'high_spending': 0,
            'custom': 0
        }
        
        validation_errors = 0
        for customer in customers:
            # Additional validation: Double-check customer belongs to selected branch
            if customer.branch:
                customer_branch_id = str(customer.branch.id) if hasattr(customer.branch, 'id') else str(customer.branch)
                if customer_branch_id != branch_id_str:
                    # Skip customers that don't match the selected branch (shouldn't happen, but safety check)
                    print(f"[Customer Segments] WARNING: Customer {customer.id} branch mismatch. Expected {branch_id_str}, got {customer_branch_id}")
                    validation_errors += 1
                    continue
            else:
                print(f"[Customer Segments] WARNING: Customer {customer.id} has no branch!")
                validation_errors += 1
                continue
            
            segment = calculate_customer_segment(customer)
            if segment in segments:
                segments[segment] += 1
        
        # Debug logging
        print(f"[Customer Segments] Branch: {branch.name} (ID: {branch_id_str})")
        print(f"[Customer Segments] Segments: {segments}")
        print(f"[Customer Segments] Total customers processed: {customers.count()}")
        print(f"[Customer Segments] Validation errors (branch mismatch): {validation_errors}")
        print(f"[Customer Segments] === REQUEST END ===\n")
        
        response = jsonify({'segments': segments})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# WhatsApp Template Routes
@customer_lifecycle_bp.route('/whatsapp-templates', methods=['GET'])
@require_role('manager', 'owner')
def list_templates(current_user=None):
    """List WhatsApp templates"""
    try:
        status = request.args.get('status')
        query = Q()
        if status:
            query &= Q(status=status)
        
        templates = WhatsAppTemplate.objects(query).order_by('-created_at')
        result = [to_dict(t) for t in templates]
        
        response = jsonify({'templates': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_lifecycle_bp.route('/whatsapp-templates', methods=['POST'])
@require_role('manager', 'owner')
def create_template(current_user=None):
    """Create a new WhatsApp template (requires approval)"""
    try:
        data = request.json
        
        template = WhatsAppTemplate(
            name=data.get('name'),
            message_text=data.get('message_text'),
            category=data.get('category', 'promotional'),
            status='inactive'  # Requires approval
        )
        template.save()
        
        result = to_dict(template)
        response = jsonify({'template': result, 'message': 'Template created. Awaiting approval.'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_lifecycle_bp.route('/whatsapp-templates/<template_id>/approve', methods=['PUT'])
@require_role('manager', 'owner')
def approve_template(template_id, current_user=None):
    """Approve a WhatsApp template"""
    try:
        template = WhatsAppTemplate.objects(id=template_id).first()
        if not template:
            response = jsonify({'error': 'Template not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # Get approving manager
        from models import Manager
        if current_user and current_user.get('user_type') == 'manager':
            manager = Manager.objects(id=current_user['id']).first()
            if manager:
                template.approved_by = manager
        
        template.status = 'active'
        template.save()
        
        result = to_dict(template)
        response = jsonify({'template': result, 'message': 'Template approved'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@customer_lifecycle_bp.route('/whatsapp-messages', methods=['GET'])
@require_role('manager', 'owner')
def list_messages(current_user=None):
    """List sent WhatsApp messages"""
    try:
        customer_id = request.args.get('customer_id')
        segment = request.args.get('segment')
        status = request.args.get('status')
        
        query = Q()
        if customer_id:
            query &= Q(customer=customer_id)
        if segment:
            query &= Q(segment=segment)
        if status:
            query &= Q(delivery_status=status)
        
        messages = WhatsAppMessage.objects(query).order_by('-sent_at')
        result = [to_dict(m) for m in messages]
        
        response = jsonify({'messages': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

