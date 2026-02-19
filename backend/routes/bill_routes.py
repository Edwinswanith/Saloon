from flask import Blueprint, request, jsonify, make_response
from models import Bill, Customer, Product, BillItemEmbedded, DiscountApprovalRequest, ApprovalCode, Staff, Membership, Branch, CashTransaction, Service, Package, MembershipPlan, ReferralProgramSettings, Referral, Invoice
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from mongoengine import Q
from utils.auth import get_current_user, require_auth, JWT_SECRET
from utils.branch_filter import get_selected_branch
from utils.date_utils import get_ist_date_range
import uuid
import re
from utils.approval_codes import hash_approval_code, is_code_expired, can_use_code

# Discount limits by role - Only owner can apply discounts
DISCOUNT_LIMITS = {
    'staff': 0,      # No discount access
    'manager': 0,   # No discount access
    'owner': 100    # Unlimited (only owner)
}

bill_bp = Blueprint('bill', __name__)

def is_mobile_device():
    """Detect if the request is from a mobile device based on User-Agent"""
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_patterns = [
        r'android', r'iphone', r'ipad', r'ipod',
        r'blackberry', r'windows phone', r'mobile',
        r'opera mini', r'opera mobi', r'fennec'
    ]
    return any(re.search(pattern, user_agent) for pattern in mobile_patterns)

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

def generate_bill_number():
    """Generate unique bill number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4().hex[:4]).upper()
    return f"BILL-{timestamp}-{random_suffix}"

def generate_invoice_number():
    """Generate sequential invoice number in format INV-000400"""
    try:
        # Find the highest existing invoice number to avoid duplicates
        last_invoice = Invoice.objects.order_by('-invoice_number').first()
        if last_invoice and last_invoice.invoice_number:
            # Extract number from last invoice (e.g., "INV-000015" -> 15)
            try:
                last_num = int(last_invoice.invoice_number.replace('INV-', '').lstrip('0') or '0')
                invoice_num = last_num + 1
            except (ValueError, AttributeError):
                # Fallback: count existing invoices
                invoice_num = Invoice.objects.count() + 1
        else:
            # No invoices exist, start from 1
            invoice_num = 1
        
        invoice_number = f"INV-{invoice_num:06d}"
        
        # Double-check for duplicates (race condition protection)
        while Invoice.objects(invoice_number=invoice_number).first():
            invoice_num += 1
            invoice_number = f"INV-{invoice_num:06d}"
        
        return invoice_number
    except Exception as e:
        # Fallback to timestamp-based if error occurs
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"INV-{timestamp[:6]}"

def _get_raw_ref_id(embedded_item, field_name):
    """Extract raw ObjectId from an EmbeddedDocument's field without triggering lazy load.

    Uses _data dict to bypass MongoEngine's dereference mechanism.
    """
    try:
        raw = embedded_item._data.get(field_name)
        if raw is None:
            return None
        # raw might be an ObjectId directly, or a DBRef, or a lazy-ref wrapper
        if isinstance(raw, ObjectId):
            return raw
        if hasattr(raw, 'id'):
            return raw.id
        if hasattr(raw, 'pk'):
            return raw.pk
    except Exception:
        pass
    return None


def _resolve_bill_items(bill):
    """Batch-resolve all bill item references in 4 queries instead of N*4.

    Returns list of item dicts ready for JSON serialization.
    """
    items_raw = bill.items or []
    if not items_raw:
        return []

    # Collect unique IDs by type using _data dict (avoids triggering lazy loads)
    service_ids = set()
    package_ids = set()
    product_ids = set()
    membership_ids = set()
    staff_ids = set()

    for item in items_raw:
        ref_id = _get_raw_ref_id(item, 'service')
        if ref_id:
            service_ids.add(ref_id)
        ref_id = _get_raw_ref_id(item, 'package')
        if ref_id:
            package_ids.add(ref_id)
        ref_id = _get_raw_ref_id(item, 'product')
        if ref_id:
            product_ids.add(ref_id)
        ref_id = _get_raw_ref_id(item, 'membership')
        if ref_id:
            membership_ids.add(ref_id)
        ref_id = _get_raw_ref_id(item, 'staff')
        if ref_id:
            staff_ids.add(ref_id)

    # Batch fetch in 4 queries (only if IDs exist)
    service_map = {}
    if service_ids:
        for svc in Service.objects(id__in=list(service_ids)):
            service_map[str(svc.id)] = svc.name

    package_map = {}
    if package_ids:
        for pkg in Package.objects(id__in=list(package_ids)):
            package_map[str(pkg.id)] = pkg.name

    product_map = {}
    if product_ids:
        for prod in Product.objects(id__in=list(product_ids)):
            product_map[str(prod.id)] = prod.name

    membership_map = {}
    if membership_ids:
        for m in Membership.objects(id__in=list(membership_ids)):
            membership_map[str(m.id)] = m.name

    staff_map = {}
    if staff_ids:
        for s in Staff.objects(id__in=list(staff_ids)):
            staff_map[str(s.id)] = f"{s.first_name or ''} {s.last_name or ''}".strip()

    # Build item list
    items = []
    for idx, item in enumerate(items_raw):
        item_type = item.item_type or 'service'

        # Resolve name: 1) denormalized name, 2) batch-fetched name, 3) fallback
        item_name = item.name if hasattr(item, 'name') and item.name else None
        if not item_name:
            ref_id = _get_raw_ref_id(item, 'service')
            if item_type == 'service' and ref_id:
                item_name = service_map.get(str(ref_id), 'Service')
            ref_id = _get_raw_ref_id(item, 'package')
            if item_type == 'package' and ref_id:
                item_name = package_map.get(str(ref_id), 'Package')
            ref_id = _get_raw_ref_id(item, 'product')
            if item_type == 'product' and ref_id:
                item_name = product_map.get(str(ref_id), 'Product')
            ref_id = _get_raw_ref_id(item, 'membership')
            if item_type == 'membership' and ref_id:
                item_name = membership_map.get(str(ref_id), 'Membership')
        if not item_name:
            item_name = 'Membership' if item_type == 'membership' else 'Item'

        # Resolve staff name
        staff_name = 'N/A'
        staff_ref_id = _get_raw_ref_id(item, 'staff')
        if staff_ref_id:
            staff_name = staff_map.get(str(staff_ref_id), 'N/A')

        # Calculate proportional tax
        item_tax = 0.0
        if bill.tax_amount and bill.subtotal and float(bill.subtotal) > 0:
            item_tax = (float(item.total or 0) / float(bill.subtotal)) * float(bill.tax_amount)

        items.append({
            'id': idx + 1,
            'name': item_name,
            'type': item_type,
            'staff_name': staff_name,
            'quantity': int(item.quantity) if item.quantity else 1,
            'price': float(item.price) if item.price else 0.0,
            'tax': round(item_tax, 2),
            'discount': float(item.discount) if item.discount else 0.0,
            'total': float(item.total) if item.total else 0.0,
            'start_time': item.start_time if item.start_time else None
        })

    return items


def _resolve_bill_metadata(bill):
    """Resolve customer and branch data for a bill. Returns (customer_data, branch_data)."""
    customer_data = {'id': None, 'name': 'Walk-in', 'mobile': None, 'wallet_balance': 0}
    if bill.customer:
        try:
            bill.customer.reload()
            customer_data = {
                'id': str(bill.customer.id),
                'name': f"{bill.customer.first_name or ''} {bill.customer.last_name or ''}".strip() or 'Walk-in',
                'mobile': bill.customer.mobile,
                'wallet_balance': float(bill.customer.wallet_balance) if hasattr(bill.customer, 'wallet_balance') and bill.customer.wallet_balance else 0
            }
        except Exception:
            pass

    branch_data = {'name': 'Saloon', 'address': '', 'city': '', 'phone': '', 'gstin': ''}
    if bill.branch:
        try:
            bill.branch.reload()
            branch_data = {
                'name': bill.branch.name or 'Saloon',
                'address': bill.branch.address or '',
                'city': bill.branch.city or '',
                'phone': bill.branch.phone or '',
                'gstin': bill.branch.gstin or ''
            }
        except Exception:
            pass

    return customer_data, branch_data


def _build_invoice_data(bill):
    """Build complete invoice data dict for a bill. Used by all invoice endpoints."""
    customer_data, branch_data = _resolve_bill_metadata(bill)
    items = _resolve_bill_items(bill)

    # Generate invoice number
    invoice_number = getattr(bill, 'invoice_number', None)
    if not invoice_number:
        try:
            # Find the highest existing invoice number to avoid duplicates
            last_invoice = Invoice.objects.order_by('-invoice_number').first()
            if last_invoice and last_invoice.invoice_number:
                # Extract number from last invoice (e.g., "INV-000015" -> 15)
                try:
                    last_num = int(last_invoice.invoice_number.replace('INV-', '').lstrip('0') or '0')
                    invoice_num = last_num + 1
                except (ValueError, AttributeError):
                    # Fallback: count existing invoices
                    invoice_num = Invoice.objects.count() + 1
            else:
                # No invoices exist, start from 1
                invoice_num = 1
            
            invoice_number = f"INV-{invoice_num:06d}"
            
            # Double-check for duplicates (race condition protection)
            while Invoice.objects(invoice_number=invoice_number).first():
                invoice_num += 1
                invoice_number = f"INV-{invoice_num:06d}"
        except Exception:
            invoice_number = f"INV-{bill.bill_number[-6:]}" if bill.bill_number else generate_invoice_number()

    # Format dates
    bill_date = bill.bill_date
    booking_date_str = 'N/A'
    booking_time_str = 'N/A'

    if bill_date:
        booking_date_str = bill_date.strftime('%a, %d %b, %Y')
        if items and items[0].get('start_time'):
            try:
                time_parts = items[0]['start_time'].split(':')
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    from datetime import time as dt_time
                    time_obj = dt_time(hour, minute)
                    booking_time_str = time_obj.strftime('%I:%M %p').lower()
            except Exception:
                booking_time_str = bill_date.strftime('%I:%M %p').lower()
        else:
            booking_time_str = bill_date.strftime('%I:%M %p').lower()

    return {
        'invoice_number': invoice_number,
        'bill_number': bill.bill_number,
        'bill_date': bill.bill_date.isoformat() if bill.bill_date else None,
        'booking_date': booking_date_str,
        'booking_time': booking_time_str,
        'customer': customer_data,
        'branch': branch_data,
        'items': items,
        'summary': {
            'subtotal': float(bill.subtotal) if bill.subtotal else 0.0,
            'discount': float(bill.discount_amount) if bill.discount_amount else 0.0,
            'referral_discount': float(bill.referral_discount) if bill.referral_discount else 0.0,
            'net': float(bill.subtotal or 0) - float(bill.discount_amount or 0) - float(bill.referral_discount or 0),
            'tax': float(bill.tax_amount) if bill.tax_amount else 0.0,
            'tax_rate': float(bill.tax_rate) if bill.tax_rate else 0.0,
            'total': float(bill.final_amount) if bill.final_amount else 0.0
        },
        'payment': {
            'status': 'paid' if (bill.booking_status == 'service-completed'
                                and bill.payment_mode
                                and bill.final_amount and bill.final_amount > 0) else 'pending',
            'mode': bill.payment_mode or 'cash',
            'amount': float(bill.final_amount) if bill.final_amount else 0,
            'source': f"{bill.payment_mode or 'Cash'}: \u20b9{bill.final_amount or 0}" if (bill.payment_mode and bill.final_amount and bill.final_amount > 0) else 'Not paid'
        }
    }


def resolve_bill_branch(current_user=None, appointment=None, customer=None):
    """Best-effort branch resolution for bills.
    
    Priority:
    1. User's explicitly selected branch (from X-Branch-Id header or get_selected_branch)
    2. Appointment branch (if no explicit branch selected)
    3. Customer branch (if no explicit branch selected)
    4. None (should not happen for authenticated users)
    """
    # PRIORITY 1: User's explicitly selected branch (from headers or user assignment)
    branch = None
    if current_user:
        branch = get_selected_branch(request, current_user)
    
    # If no explicit branch selected, try appointment branch
    if not branch and appointment and getattr(appointment, 'branch', None):
        branch = appointment.branch
    
    # If still no branch, try customer branch
    if not branch and customer and getattr(customer, 'branch', None):
        branch = customer.branch
    
    return branch

@bill_bp.route('/bills', methods=['GET'])
@require_auth
def get_bills(current_user=None):
    """Get bills with optional filters - OPTIMIZED with pagination"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        appointment_id = request.args.get('appointment_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        payment_mode = request.args.get('payment_mode')
        booking_status = request.args.get('booking_status')
        include_deleted = request.args.get('include_deleted', type=bool, default=False)

        # OPTIMIZED: Add pagination parameters with sensible defaults
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 per page

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Bill.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if not include_deleted:
            query = query.filter(is_deleted=False)
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                query = query.filter(customer=customer)
            except Customer.DoesNotExist:
                pass
        if appointment_id:
            from models import Appointment
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                query = query.filter(appointment=appointment)
            except Appointment.DoesNotExist:
                pass
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                query = query.filter(bill_date__gte=start)
            if end:
                query = query.filter(bill_date__lte=end)
        if payment_mode:
            query = query.filter(payment_mode=payment_mode)
        if booking_status:
            query = query.filter(booking_status=booking_status)

        # OPTIMIZED: Get count first, then paginate
        total = query.count()
        bills = list(query.order_by('-bill_date').skip((page - 1) * per_page).limit(per_page))

        result = []
        for b in bills:
            try:
                customer_info = get_safe_customer_info(b.customer)
                customer_name = customer_info['name']
                customer_mobile = customer_info['mobile']
                customer_obj_id = customer_info['id']

                bill_data = {
                    'id': str(b.id),
                    'bill_number': b.bill_number,
                    'customer_id': customer_obj_id,
                    'customer_name': customer_name,
                    'customer_mobile': customer_mobile,
                    'bill_date': b.bill_date.isoformat() if b.bill_date else None,
                    'subtotal': b.subtotal,
                    'discount_amount': b.discount_amount,
                    'discount_type': b.discount_type,
                    'tax_amount': b.tax_amount,
                    'tax_rate': b.tax_rate,
                    'final_amount': b.final_amount,
                    'payment_mode': b.payment_mode,
                    'booking_status': b.booking_status,
                    'booking_note': b.booking_note,
                    'is_deleted': b.is_deleted,
                    'created_at': b.created_at.isoformat() if b.created_at else None
                }

                # Include items when filtering by appointment_id (for edit functionality)
                if appointment_id and b.items:
                    bill_data['items'] = []
                    for item in b.items:
                        item_data = {
                            'item_type': item.item_type,
                            'name': item.name or '',
                            'price': item.price,
                            'discount': item.discount,
                            'quantity': item.quantity,
                            'total': item.total,
                            'start_time': item.start_time,
                        }
                        # Add reference IDs based on item type
                        if item.service:
                            item_data['service_id'] = str(item.service.id)
                            if item.service.name:
                                item_data['name'] = item.service.name
                        if item.package:
                            item_data['package_id'] = str(item.package.id)
                            if item.package.name:
                                item_data['name'] = item.package.name
                        if item.product:
                            item_data['product_id'] = str(item.product.id)
                            if item.product.name:
                                item_data['name'] = item.product.name
                        if item.membership:
                            item_data['membership_id'] = str(item.membership.id)
                            if item.membership.name:
                                item_data['name'] = item.membership.name
                        elif item.item_type == 'membership' and item.name:
                            # Before checkout, membership ref is None; look up plan by name
                            try:
                                plan = MembershipPlan.objects(name=item.name).first()
                                if plan:
                                    item_data['membership_id'] = str(plan.id)
                            except:
                                pass
                        if item.staff:
                            item_data['staff_id'] = str(item.staff.id)
                        # Fallback for membership items with missing names (legacy data)
                        if item.item_type == 'membership' and not item_data.get('name'):
                            try:
                                from models import MembershipPlan
                                plan = MembershipPlan.objects(price=item.price).first()
                                if plan:
                                    item_data['name'] = plan.name
                                    item_data['membership_id'] = str(plan.id)
                            except:
                                pass
                        bill_data['items'].append(item_data)

                result.append(bill_data)
            except Exception as e:
                print(f"Error processing bill {b.id}: {e}")
                continue

        # Return with pagination metadata
        return jsonify({
            'bills': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<id>', methods=['GET'])
def get_bill(id):
    """Get a single bill with items"""
    try:
        bill = Bill.objects.get(id=id)
        
        customer_info = get_safe_customer_info(bill.customer)
        customer_name = customer_info['name']
        customer_mobile = customer_info['mobile']
        customer_obj_id = customer_info['id']

        items = []
        for idx, item in enumerate(bill.items or []):
            # Safely get service info
            service_id = None
            service_name = None
            try:
                service_ref = getattr(item, 'service', None)
                if service_ref:
                    if hasattr(service_ref, 'reload'):
                        service_ref.reload()
                    service_id = str(service_ref.id) if hasattr(service_ref, 'id') else None
                    service_name = getattr(service_ref, 'name', None)
            except Exception as e:
                print(f"Error loading service for bill item {idx}: {e}")

            # Safely get package info
            package_id = None
            package_name = None
            try:
                package_ref = getattr(item, 'package', None)
                if package_ref:
                    if hasattr(package_ref, 'reload'):
                        package_ref.reload()
                    package_id = str(package_ref.id) if hasattr(package_ref, 'id') else None
                    package_name = getattr(package_ref, 'name', None)
            except Exception as e:
                print(f"Error loading package for bill item {idx}: {e}")

            # Safely get product info
            product_id = None
            product_name = None
            try:
                product_ref = getattr(item, 'product', None)
                if product_ref:
                    if hasattr(product_ref, 'reload'):
                        product_ref.reload()
                    product_id = str(product_ref.id) if hasattr(product_ref, 'id') else None
                    product_name = getattr(product_ref, 'name', None)
            except Exception as e:
                print(f"Error loading product for bill item {idx}: {e}")

            # Safely get staff info
            staff_id = None
            staff_name = None
            try:
                staff_ref = getattr(item, 'staff', None)
                if staff_ref:
                    if hasattr(staff_ref, 'reload'):
                        staff_ref.reload()
                    staff_id = str(staff_ref.id) if hasattr(staff_ref, 'id') else None
                    first_name = getattr(staff_ref, 'first_name', '') or ''
                    last_name = getattr(staff_ref, 'last_name', '') or ''
                    staff_name = f"{first_name} {last_name}".strip() or None
            except Exception as e:
                print(f"Error loading staff for bill item {idx}: {e}")

            item_data = {
                'id': idx,  # Index as ID for embedded documents
                'item_type': getattr(item, 'item_type', None),
                'service_id': service_id,
                'service_name': service_name,
                'package_id': package_id,
                'package_name': package_name,
                'product_id': product_id,
                'product_name': product_name,
                'staff_id': staff_id,
                'staff_name': staff_name,
                'start_time': getattr(item, 'start_time', None),
                'price': getattr(item, 'price', 0),
                'discount': getattr(item, 'discount', 0),
                'quantity': getattr(item, 'quantity', 1),
                'total': getattr(item, 'total', 0)
            }
            items.append(item_data)

        return jsonify({
            'id': str(bill.id),
            'bill_number': bill.bill_number,
            'customer_id': customer_obj_id,
            'customer_name': customer_name,
            'customer_mobile': customer_mobile,
            'bill_date': bill.bill_date.isoformat() if bill.bill_date else None,
            'subtotal': bill.subtotal,
            'discount_amount': bill.discount_amount,
            'discount_type': bill.discount_type,
            'tax_amount': bill.tax_amount,
            'tax_rate': bill.tax_rate,
            'final_amount': bill.final_amount,
            'payment_mode': bill.payment_mode,
            'booking_status': bill.booking_status,
            'booking_note': bill.booking_note,
            'is_deleted': bill.is_deleted,
            'deleted_at': bill.deleted_at.isoformat() if bill.deleted_at else None,
            'deletion_reason': bill.deletion_reason,
            'items': items,
            'created_at': bill.created_at.isoformat() if bill.created_at else None,
            'updated_at': bill.updated_at.isoformat() if bill.updated_at else None
        })
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills', methods=['POST'])
def create_bill():
    """Create a new bill (draft) or return existing unchecked-out bill for appointment"""
    try:
        data = request.get_json()
        current_user = get_current_user()

        # Check if appointment_id is provided and if existing unchecked-out bill exists
        appointment_id = data.get('appointment_id')
        appointment = None
        existing_bill = None
        
        if appointment_id:
            from models import Appointment
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                # Find existing unchecked-out bill for this appointment
                # Unchecked-out means: booking_status != 'service-completed' OR payment_mode is None
                existing_bills = Bill.objects(
                    appointment=appointment,
                    is_deleted=False
                ).order_by('-created_at')
                
                for bill in existing_bills:
                    # Check if bill is unchecked-out
                    is_checked_out = (bill.booking_status == 'service-completed' and bill.payment_mode)
                    if not is_checked_out:
                        existing_bill = bill
                        break
            except Appointment.DoesNotExist:
                pass
            except Exception as e:
                # Log error but continue to create new bill
                print(f"Error checking for existing bill: {e}")
        
        # If existing unchecked-out bill found, clear old items and return it
        if existing_bill:
            # Clear previous items so only current selections are added
            existing_bill.items = []
            if not existing_bill.branch:
                branch = resolve_bill_branch(
                    current_user=current_user,
                    appointment=appointment,
                    customer=existing_bill.customer
                )
                if branch:
                    existing_bill.branch = branch
            existing_bill.save()
            return jsonify({
                'id': str(existing_bill.id),
                'message': 'Using existing bill for appointment',
                'data': {
                    'id': str(existing_bill.id),
                    'bill_number': existing_bill.bill_number,
                    'existing': True
                }
            }), 200

        customer = None
        if data.get('customer_id'):
            try:
                customer = Customer.objects.get(id=data['customer_id'])
            except Customer.DoesNotExist:
                response = jsonify({'error': 'Customer not found. Please re-select the customer.'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400

        # Handle bill_date - use provided date or current UTC time
        bill_date = datetime.utcnow()
        if data.get('bill_date'):
            # If bill_date is provided as a date string (YYYY-MM-DD), convert to UTC datetime
            try:
                date_str = data.get('bill_date')
                if isinstance(date_str, str) and len(date_str) == 10:  # YYYY-MM-DD format
                    # Parse as local date and convert to UTC
                    # Assuming IST (UTC+5:30), local date "2026-01-06" means UTC range
                    local_date = datetime.strptime(date_str, '%Y-%m-%d')
                    # Use noon local time (to avoid timezone edge cases) and convert to UTC
                    bill_date = local_date.replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(hours=5, minutes=30)
                else:
                    # Try parsing as ISO datetime string
                    bill_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if bill_date.tzinfo:
                        bill_date = bill_date.astimezone(timezone.utc).replace(tzinfo=None)
            except (ValueError, AttributeError):
                # If parsing fails, use current UTC time
                bill_date = datetime.utcnow()

        if appointment_id and not appointment:
            from models import Appointment
            try:
                appointment = Appointment.objects.get(id=appointment_id)
            except Appointment.DoesNotExist:
                pass

        branch = resolve_bill_branch(
            current_user=current_user,
            appointment=appointment,
            customer=customer
        )

        bill = Bill(
            bill_number=generate_bill_number(),
            customer=customer,
            appointment=appointment,
            branch=branch,
            bill_date=bill_date,
            subtotal=0,
            discount_amount=0,
            tax_amount=0,
            final_amount=0,
            booking_status=data.get('booking_status', 'pending'),
            booking_note=data.get('booking_note'),
            items=[]
        )
        bill.save()

        return jsonify({
            'id': str(bill.id),
            'message': 'Bill created successfully',
            'data': {
                'id': str(bill.id),
                'bill_number': bill.bill_number,
                'existing': False
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<id>/items', methods=['POST'])
def add_bill_item(id):
    """Add item to bill"""
    try:
        # Validate bill ID format
        if not id or len(id) < 10:
            return jsonify({'error': f'Invalid bill ID format: {id}'}), 400
        
        bill = Bill.objects.get(id=id)
        data = request.get_json()

        # Get start time as string (model expects StringField)
        start_time = None
        if 'start_time' in data and data['start_time']:
            start_time = data['start_time']  # Keep as string in HH:MM:SS format

        # Get references
        service = None
        package = None
        product = None
        membership = None
        staff = None
        item_name = None

        from models import Service, Package, Membership, MembershipPlan, Staff as StaffModel
        
        # Ensure bill has a branch assigned
        if not bill.branch:
            current_user = get_current_user()
            appointment = None
            if bill.appointment:
                try:
                    bill.appointment.reload()
                    appointment = bill.appointment
                except Exception:
                    appointment = bill.appointment
            branch = resolve_bill_branch(
                current_user=current_user,
                appointment=appointment,
                customer=bill.customer
            )
            if branch:
                bill.branch = branch
                bill.save()
            else:
                return jsonify({'error': 'Bill must have a branch assigned before adding items'}), 400
        
        if data.get('service_id'):
            try:
                service = Service.objects.get(id=data['service_id'])
                # Validate: reject if service belongs to a DIFFERENT branch (allow legacy items with no branch)
                if bill.branch and service.branch and str(service.branch.id) != str(bill.branch.id):
                    return jsonify({'error': 'Service does not belong to this branch'}), 400
            except Service.DoesNotExist:
                return jsonify({'error': 'Service not found'}), 404
        if data.get('package_id'):
            try:
                package = Package.objects.get(id=data['package_id'])
                # Validate: reject if package belongs to a DIFFERENT branch (allow legacy items with no branch)
                if bill.branch and package.branch and str(package.branch.id) != str(bill.branch.id):
                    return jsonify({'error': 'Package does not belong to this branch'}), 400
            except Package.DoesNotExist:
                return jsonify({'error': 'Package not found'}), 404
        if data.get('product_id'):
            try:
                product = Product.objects.get(id=data['product_id'])
                # Validate: reject if product belongs to a DIFFERENT branch (allow legacy items with no branch)
                if bill.branch and product.branch and str(product.branch.id) != str(bill.branch.id):
                    return jsonify({'error': 'Product does not belong to this branch'}), 400
            except Product.DoesNotExist:
                return jsonify({'error': 'Product not found'}), 404
        if data.get('membership_id'):
            try:
                membership_plan = MembershipPlan.objects.get(id=data['membership_id'])
                item_name = membership_plan.name
            except MembershipPlan.DoesNotExist:
                # Try to find by name if ID lookup fails
                if data.get('name'):
                    membership_plan = MembershipPlan.objects(name=data['name'], status='active').first()
                    if membership_plan:
                        item_name = membership_plan.name
                    else:
                        return jsonify({'error': f'Membership plan not found: {data.get("name", "unknown")}'}), 404
                else:
                    return jsonify({'error': 'Membership plan not found'}), 404
            except Exception as e:
                # If ID lookup fails with other error, try name fallback
                if data.get('name'):
                    membership_plan = MembershipPlan.objects(name=data['name'], status='active').first()
                    if membership_plan:
                        item_name = membership_plan.name
                    else:
                        return jsonify({'error': f'Membership plan not found: {data.get("name", "unknown")}'}), 404
                else:
                    return jsonify({'error': f'Membership plan lookup error: {str(e)}'}), 500
        elif data.get('item_type') == 'membership' and data.get('name') and not data.get('membership_id'):
            # Handle case where only name is provided (no membership_id)
            membership_plan = MembershipPlan.objects(name=data['name'], status='active').first()
            if membership_plan:
                item_name = membership_plan.name
            else:
                return jsonify({'error': f'Membership plan not found: {data.get("name", "unknown")}'}), 404
        if data.get('staff_id'):
            try:
                staff = StaffModel.objects.get(id=data['staff_id'])
            except:
                pass

        # Determine item name based on item type (for denormalized storage)
        # Note: item_name may already be set from MembershipPlan lookup above
        if service:
            item_name = service.name
        elif package:
            item_name = package.name
        elif product:
            item_name = product.name

        # Final fallback: use name from request data (frontend sends it for memberships)
        if not item_name:
            item_name = data.get('name')

        item = BillItemEmbedded(
            item_type=data['item_type'],
            name=item_name,
            service=service,
            package=package,
            product=product,
            membership=membership,
            staff=staff,
            start_time=start_time,
            price=data['price'],
            discount=data.get('discount', 0),
            quantity=data.get('quantity', 1),
            total=data['total']
        )

        # Validate product stock availability (but don't reduce stock yet - will be reduced on checkout)
        if product and data.get('quantity'):
            quantity_requested = int(data.get('quantity', 1))
            if product.stock_quantity is not None:
                if product.stock_quantity < quantity_requested:
                    return jsonify({
                        'error': f'Insufficient stock. Only {product.stock_quantity} units available'
                    }), 400

        # Use atomic $push to avoid race condition when adding items in parallel
        result = Bill.objects(id=id).update_one(push__items=item)
        print(f"[ADD_ITEM] Bill {id}: $push result={result}, item_type={data['item_type']}, name={item_name}")
        bill.reload()
        print(f"[ADD_ITEM] Bill {id}: after reload, items count={len(bill.items)}, items={[i.name for i in bill.items]}")

        return jsonify({
            'id': len(bill.items) - 1,  # Return index
            'message': 'Item added to bill successfully',
            'product_stock_validated': product is not None
        }), 201
    except Bill.DoesNotExist:
        return jsonify({'error': f'Bill not found with ID: {id}'}), 404
    except Exception as e:
        import traceback
        print(f"[ADD_ITEM] Error adding item to bill {id}: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<bill_id>/items/<int:item_id>', methods=['DELETE'])
def remove_bill_item(bill_id, item_id):
    """Remove item from bill"""
    try:
        bill = Bill.objects.get(id=bill_id)
        
        if item_id < 0 or item_id >= len(bill.items):
            return jsonify({'error': 'Item not found'}), 404
        
        bill.items.pop(item_id)
        bill.save()

        return jsonify({'message': 'Item removed from bill successfully'})
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<id>/checkout', methods=['POST'])
@require_auth
def checkout_bill(id, current_user=None):
    """Complete checkout process for a bill"""
    try:
        bill = Bill.objects.get(id=id)
        data = request.get_json()
        
        # Validate required fields
        if not data:
            print(f"[CHECKOUT] Error: Request body is missing for bill {id}")
            return jsonify({'error': 'Request body is required'}), 400
        
        if 'payment_mode' not in data or not data.get('payment_mode'):
            print(f"[CHECKOUT] Error: payment_mode is missing for bill {id}. Data: {data}")
            return jsonify({'error': 'payment_mode is required'}), 400

        print(f"[CHECKOUT] Processing checkout for bill {id}, payment_mode: {data.get('payment_mode')}")

        # Check if bill is already checked out to prevent double stock reduction
        is_already_checked_out = (bill.booking_status == 'service-completed' and bill.payment_mode)

        # Get current user and check permissions
        current_user = get_current_user()
        user_role = current_user.get('role') if current_user else 'staff'
        
        # Validate bill has items
        if not bill.items or len(bill.items) == 0:
            print(f"[CHECKOUT] Error: Bill {id} has no items")
            return jsonify({'error': 'Bill must have at least one item before checkout'}), 400

        # Calculate subtotal from items
        subtotal = sum([float(item.total) if item.total else 0.0 for item in bill.items])
        subtotal = float(subtotal) if subtotal else 0.0
        
        print(f"[CHECKOUT] Bill {id} subtotal: {subtotal}, items count: {len(bill.items)}")

        # Resolve bill branch early — must happen before any approval request is created
        # so that DiscountApprovalRequest.branch is set correctly and owners can find it
        # via the branch filter in the Discount Approvals page.
        if not bill.branch:
            _appointment = None
            if bill.appointment:
                try:
                    bill.appointment.reload()
                    _appointment = bill.appointment
                except Exception:
                    _appointment = bill.appointment
            _resolved_branch = resolve_bill_branch(
                current_user=current_user,
                appointment=_appointment,
                customer=bill.customer
            )
            if _resolved_branch:
                bill.branch = _resolved_branch
                print(f"[CHECKOUT] Resolved bill branch early: {_resolved_branch.name} (ID: {_resolved_branch.id})")

        # Check for active membership discount first (automatic, cannot be overridden)
        membership_discount_applied = False
        discount_amount = 0.0
        discount_type = 'fix'
        
        if bill.customer:
            # OPTIMIZE: Use indexed query for faster lookup
            bill.customer.reload()
            active_membership = Membership.objects(
                customer=bill.customer,
                status='active',
                expiry_date__gte=datetime.utcnow()
            ).first()
            
            if active_membership and active_membership.plan:
                # Reload plan to get allocated_discount
                active_membership.plan.reload()
                if active_membership.plan.allocated_discount > 0:
                    # Apply membership discount automatically
                    membership_discount_percent = float(active_membership.plan.allocated_discount)
                    discount_amount = float(subtotal) * (membership_discount_percent / 100.0)
                    discount_type = 'membership'
                    membership_discount_applied = True
        
        # If no membership discount, check for manual discount
        if not membership_discount_applied:
            # Get discount from request
            discount_amount = float(data.get('discount_amount', 0) or 0)
            discount_type = data.get('discount_type', 'fix')

            # Calculate discount percentage for manual discounts
            discount_percent = 0
            if discount_type == 'percentage':
                discount_percent = float(discount_amount)
                discount_amount = float(subtotal) * (float(discount_amount) / 100.0)
            elif discount_amount > 0 and subtotal > 0:
                discount_percent = (discount_amount / subtotal) * 100

            # Calculate item-level discounts (per-service/package/product discount %)
            item_level_discount = 0
            for item in (bill.items or []):
                item_disc = float(item.discount or 0)
                item_price = float(item.price or 0)
                if item_disc > 0 and item_price > 0:
                    item_level_discount += item_price * item_disc / 100.0

            # Total discount = bill-level + item-level
            total_discount_for_approval = discount_amount + item_level_discount

            # If only item-level discount, compute combined percent for the approval record
            if total_discount_for_approval > 0 and discount_percent == 0 and subtotal > 0:
                discount_percent = (total_discount_for_approval / subtotal) * 100

            # Non-owner applying ANY discount → needs approval
            if total_discount_for_approval > 0 and user_role != 'owner':
                approval_code_input = (data.get('approval_code') or '').strip()

                # ALWAYS validate approval code first if one was provided,
                # regardless of whether the discount was already approved.
                # This prevents checkout with a wrong code even when the
                # owner already approved the discount from the approvals page.
                matched_code = None
                if approval_code_input:
                    code_hash = hash_approval_code(approval_code_input)
                    matched_code = ApprovalCode.objects(code_hash=code_hash, is_active=True).first()

                    code_error = None
                    if not matched_code:
                        code_error = 'Invalid approval code'
                    elif is_code_expired(matched_code.expires_at):
                        code_error = 'Approval code has expired'
                    elif not can_use_code(matched_code.usage_count, matched_code.max_uses):
                        code_error = 'Approval code has reached its usage limit'

                    if code_error:
                        print(f"[CHECKOUT] Approval code rejected for bill {id}: {code_error}")
                        response = jsonify({
                            'error': code_error,
                            'code_invalid': True,
                            'requires_approval': True,
                            'message': code_error
                        })
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 400

                # Check if an approved approval already exists for this bill
                approved = DiscountApprovalRequest.objects(
                    bill=bill, approval_status='approved'
                ).first()

                if not approved:
                    if approval_code_input and matched_code:
                        # Code is valid — create or update approval as approved
                        staff_ref = None
                        if current_user.get('user_type') == 'staff':
                            try:
                                staff_ref = Staff.objects(id=current_user['user_id']).first()
                            except Exception:
                                pass

                        # Find existing pending request or create new one
                        approval_req = DiscountApprovalRequest.objects(
                            bill=bill, approval_status='pending'
                        ).first()

                        if approval_req:
                            approval_req.approval_status = 'approved'
                            approval_req.approval_method = 'code'
                            approval_req.approval_code_used = matched_code.code_hash
                            approval_req.approved_at = datetime.utcnow()
                            approval_req.updated_at = datetime.utcnow()
                            approval_req.save()
                        else:
                            approval_req = DiscountApprovalRequest(
                                bill=bill,
                                requested_by=staff_ref,
                                requested_by_name=current_user.get('name', 'Unknown'),
                                requested_by_role=user_role,
                                branch=bill.branch,
                                requested_discount_percent=discount_percent,
                                requested_discount_amount=total_discount_for_approval,
                                reason=data.get('discount_reason', 'Discount requested'),
                                approval_status='approved',
                                approval_method='code',
                                approval_code_used=matched_code.code_hash,
                                approved_at=datetime.utcnow(),
                            )
                            approval_req.save()

                        # Increment code usage
                        matched_code.usage_count += 1
                        matched_code.save()

                        bill.discount_approval_status = 'approved'
                        bill.discount_approval_request = approval_req
                        bill.save()
                        print(f"[CHECKOUT] Discount approved via code for bill {id}")
                        # Fall through to normal checkout below

                    elif not approval_code_input:
                        # No code provided — existing pending flow
                        pending = DiscountApprovalRequest.objects(
                            bill=bill, approval_status='pending'
                        ).first()

                        if not pending:
                            # Get staff reference if user is staff
                            staff_ref = None
                            if current_user.get('user_type') == 'staff':
                                try:
                                    staff_ref = Staff.objects(id=current_user['user_id']).first()
                                except Exception:
                                    pass

                            pending = DiscountApprovalRequest(
                                bill=bill,
                                requested_by=staff_ref,
                                requested_by_name=current_user.get('name', 'Unknown'),
                                requested_by_role=user_role,
                                branch=bill.branch,
                                requested_discount_percent=discount_percent,
                                requested_discount_amount=total_discount_for_approval,
                                reason=data.get('discount_reason', 'Discount requested'),
                            )
                            pending.save()

                            bill.discount_approval_status = 'pending'
                            bill.discount_approval_request = pending
                            bill.save()
                            print(f"[CHECKOUT] Created discount approval request {pending.id} for bill {id}")

                        response = jsonify({
                            'error': 'Discount requires owner approval',
                            'requires_approval': True,
                            'approval_id': str(pending.id),
                            'message': 'Discount approval request submitted. Owner must approve before checkout.'
                        })
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 403

        # Calculate tax on amount after membership discount
        tax_rate = float(data.get('tax_rate', 0) or 0)
        amount_after_all_discounts = float(subtotal) - float(discount_amount)
        if amount_after_all_discounts < 0:
            amount_after_all_discounts = 0.0

        # Use pre-calculated tax values from frontend if provided (handles inclusive/exclusive pricing)
        if data.get('tax_amount') is not None:
            tax_amount = float(data.get('tax_amount', 0) or 0)
        else:
            tax_amount = float(amount_after_all_discounts) * (float(tax_rate) / 100.0)

        # Calculate final amount — use frontend value if provided (inclusive pricing differs)
        if data.get('final_amount') is not None:
            final_amount = float(data.get('final_amount', 0) or 0)
        else:
            final_amount = amount_after_all_discounts + tax_amount

        # Update bill_date if provided in checkout data (for selected date from frontend)
        if data.get('bill_date'):
            try:
                date_str = data.get('bill_date')
                if isinstance(date_str, str) and len(date_str) == 10:  # YYYY-MM-DD format
                    # Parse as local date and convert to UTC
                    # Assuming IST (UTC+5:30), use noon local time to avoid edge cases
                    local_date = datetime.strptime(date_str, '%Y-%m-%d')
                    # Use noon local time (to avoid timezone edge cases) and convert to UTC
                    bill.bill_date = local_date.replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(hours=5, minutes=30)
            except (ValueError, AttributeError):
                # If parsing fails, keep existing bill_date
                pass

        # Store referral discount if provided by frontend
        referral_discount = float(data.get('referral_discount', 0) or 0)

        # Update bill
        bill.subtotal = subtotal
        bill.discount_amount = discount_amount
        bill.discount_type = discount_type
        bill.referral_discount = referral_discount
        bill.tax_amount = tax_amount
        bill.tax_rate = tax_rate
        bill.final_amount = final_amount
        bill.payment_mode = data['payment_mode']
        # Always set to 'service-completed' when checkout happens to mark as paid
        bill.booking_status = 'service-completed'
        # Only reset approval status if owner is checking out without prior approval flow
        if bill.discount_approval_status not in ('approved',):
            bill.discount_approval_status = 'none'
        bill.updated_at = datetime.utcnow()

        # Update product stock - validate and reduce for all products in bill
        # Skip if bill is already checked out to prevent double stock reduction
        if not is_already_checked_out:
            products_to_update = []
            for item in bill.items:
                if item.item_type == 'product' and item.product:
                    # Reload product to get latest stock count (handles concurrent checkouts)
                    item.product.reload()
                    quantity_needed = int(item.quantity) if item.quantity else 1

                    # Validate: reject if product belongs to a DIFFERENT branch (allow legacy items with no branch)
                    if bill.branch and item.product.branch and str(item.product.branch.id) != str(bill.branch.id):
                        error_msg = f'Product {item.product.name} does not belong to this branch'
                        print(f"[CHECKOUT] Error: {error_msg} (Bill branch: {bill.branch.id if bill.branch else None}, Product branch: {item.product.branch.id if item.product.branch else None})")
                        return jsonify({'error': error_msg}), 400

                    # Validate stock availability before reducing
                    if item.product.stock_quantity is not None:
                        if item.product.stock_quantity < quantity_needed:
                            error_msg = f'Insufficient stock for product: {item.product.name}. Available: {item.product.stock_quantity}, Required: {quantity_needed}'
                            print(f"[CHECKOUT] Error: {error_msg}")
                            return jsonify({'error': error_msg}), 400

                        # Store product and quantity for batch update
                        products_to_update.append({
                            'product': item.product,
                            'quantity': quantity_needed
                        })

            # Reduce stock for all products (atomic operation - all or nothing)
            for product_update in products_to_update:
                product_update['product'].stock_quantity -= product_update['quantity']
                if product_update['product'].stock_quantity < 0:
                    product_update['product'].stock_quantity = 0  # Prevent negative stock
                product_update['product'].save()

        bill.save()

        # Create Membership records for membership items (only for new checkouts)
        if not is_already_checked_out and bill.customer:
            membership_items_updated = False
            for item in bill.items:
                if item.item_type == 'membership' and item.name:
                    try:
                        # Look up the MembershipPlan by name
                        plan = MembershipPlan.objects(name=item.name, status='active').first()
                        if not plan:
                            # Fallback: try case-insensitive match
                            plan = MembershipPlan.objects(name__iexact=item.name).first()

                        if plan:
                            # Create the Membership record for this customer
                            now = datetime.utcnow()
                            new_membership = Membership(
                                name=plan.name,
                                customer=bill.customer,
                                plan=plan,
                                branch=bill.branch,
                                price=float(item.price) if item.price else float(plan.price),
                                purchase_date=now,
                                expiry_date=now + timedelta(days=plan.validity_days),
                                status='active'
                            )
                            new_membership.save()

                            # Link the bill item to the new Membership record
                            item.membership = new_membership
                            membership_items_updated = True

                            print(f"[CHECKOUT] Created Membership '{plan.name}' for customer {bill.customer.id}, expires {new_membership.expiry_date}")
                        else:
                            print(f"[CHECKOUT] Warning: MembershipPlan not found for name '{item.name}'")
                    except Exception as e:
                        print(f"[CHECKOUT] Warning: Failed to create Membership for item '{item.name}': {e}")

            if membership_items_updated:
                bill.save()

        # Record payment transaction in cash register (all payment modes, only for new checkouts)
        cash_txn_warning = None
        if not is_already_checked_out and final_amount > 0:
            try:
                from datetime import date as date_type
                payment_mode = data['payment_mode']
                cash_txn = CashTransaction(
                    transaction_type='in',
                    branch=bill.branch,
                    amount=final_amount,
                    payment_method=payment_mode,
                    source='bill',
                    bill_ref=bill,
                    reason=f'Bill #{bill.bill_number}',
                    notes=f'{payment_mode.upper()} payment for bill {bill.bill_number}',
                    transaction_date=date_type.today(),
                    transaction_time=datetime.now().strftime('%H:%M:%S')
                )
                cash_txn.save()
            except Exception as e:
                cash_txn_warning = f'Payment recorded but cash register entry failed: {e}'
                print(f"[CHECKOUT] Warning: Failed to record cash transaction: {e}")

        # Process referral rewards (only for new checkouts)
        referral_info = None
        if not is_already_checked_out and bill.customer:
            try:
                customer = bill.customer
                customer.reload()
                # Check if customer was referred and hasn't used referral reward yet
                if customer.referred_by and not customer.referral_reward_used:
                    referral_settings = ReferralProgramSettings.get_settings()
                    if referral_settings.enabled:
                        # Calculate referee discount (already applied via frontend) and referrer reward
                        if referral_settings.reward_type == 'percentage':
                            referrer_reward_amount = float(subtotal) * (referral_settings.referrer_reward_percentage / 100.0)
                            referee_discount_amount = float(subtotal) * (referral_settings.referee_reward_percentage / 100.0)
                        else:
                            referrer_reward_amount = referral_settings.referrer_reward_percentage
                            referee_discount_amount = referral_settings.referee_reward_percentage

                        # Update the Referral record with bill and reward amounts
                        referral_record = Referral.objects(referee=customer).first()
                        if referral_record:
                            referral_record.bill = bill
                            referral_record.referee_discount = referee_discount_amount
                            referral_record.referrer_reward = referrer_reward_amount
                            referral_record.save()

                        # Mark customer as having used referral reward
                        customer.referral_reward_used = True
                        customer.save()

                        referral_info = {
                            'referrerReward': referrer_reward_amount,
                            'refereeDiscount': referee_discount_amount
                        }
                        print(f"[CHECKOUT] Referral reward processed: referee discount ₹{referee_discount_amount:.2f}, referrer reward ₹{referrer_reward_amount:.2f}")
            except Exception as e:
                print(f"[CHECKOUT] Warning: Failed to process referral reward: {e}")

        # Generate and save invoice PDF to GridFS (only for new checkouts)
        # MANDATORY: PDF generation must succeed or checkout fails
        if not is_already_checked_out:
            from services.invoice_pdf_service import generate_invoice_pdf
            from services.pdf_storage_service import save_pdf_to_gridfs
            
            # Build invoice data
            invoice_data = _build_invoice_data(bill)
            
            # Generate PDF - this must succeed
            pdf_bytes = generate_invoice_pdf(invoice_data)
            if not pdf_bytes:
                error_msg = 'Failed to generate invoice PDF'
                print(f"[CHECKOUT] Error: {error_msg}")
                return jsonify({'error': error_msg}), 500
            
            # Save to GridFS - this must succeed
            try:
                pdf_file_id = save_pdf_to_gridfs(
                    pdf_bytes=pdf_bytes,
                    bill_id=str(bill.id),
                    invoice_number=invoice_data.get('invoice_number', bill.bill_number),
                    bill_number=bill.bill_number,
                    bill_date=bill.bill_date
                )
                print(f"[CHECKOUT] PDF saved to GridFS: file_id={pdf_file_id}, size={len(pdf_bytes)} bytes")
            except Exception as e:
                error_msg = f'Failed to save invoice PDF to storage: {str(e)}'
                print(f"[CHECKOUT] Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': error_msg}), 500
            
            # Store PDF metadata in bill
            bill.pdf_file_id = pdf_file_id
            bill.pdf_generated_at = datetime.utcnow()
            bill.pdf_file_size = len(pdf_bytes)
            
            # Create Invoice document in MongoDB
            try:
                invoice = Invoice(
                    bill=bill,
                    invoice_number=invoice_data.get('invoice_number', bill.bill_number),
                    customer=bill.customer,
                    branch=bill.branch,
                    pdf_file_id=pdf_file_id,
                    invoice_data=invoice_data,
                    generated_at=datetime.utcnow(),
                    status='generated'
                )
                invoice.save()
                
                # Link Invoice to Bill
                bill.invoice = invoice
                
                print(f"[CHECKOUT] Invoice document created: invoice_id={invoice.id}, invoice_number={invoice.invoice_number}, pdf_file_id={pdf_file_id}")
            except Exception as e:
                error_msg = f'Failed to create invoice document: {str(e)}'
                print(f"[CHECKOUT] Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': error_msg}), 500
            
            # PDF already logged above when saved to GridFS

        print(f"[CHECKOUT] Success: Bill {id} checked out successfully. Final amount: {bill.final_amount}")
        checkout_result = {
            'message': 'Checkout completed successfully',
            'bill_number': bill.bill_number,
            'final_amount': bill.final_amount
        }
        if referral_info:
            checkout_result['referral'] = referral_info
        if cash_txn_warning:
            checkout_result['cash_register_warning'] = cash_txn_warning
        return jsonify(checkout_result)
    except Bill.DoesNotExist:
        print(f"[CHECKOUT] Error: Bill {id} not found")
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        error_msg = str(e)
        print(f"[CHECKOUT] Error: Exception during checkout for bill {id}: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@bill_bp.route('/bills/<id>', methods=['PUT'])
def update_bill(id):
    """Update bill details"""
    try:
        bill = Bill.objects.get(id=id)
        data = request.get_json()

        if 'customer_id' in data:
            if data['customer_id']:
                try:
                    bill.customer = Customer.objects.get(id=data['customer_id'])
                except Customer.DoesNotExist:
                    pass
            else:
                bill.customer = None
        if 'booking_status' in data:
            bill.booking_status = data['booking_status']
        if 'booking_note' in data:
            bill.booking_note = data['booking_note']
        if 'payment_mode' in data:
            bill.payment_mode = data['payment_mode']
        bill.updated_at = datetime.utcnow()
        bill.save()

        return jsonify({
            'id': str(bill.id),
            'message': 'Bill updated successfully'
        })
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<id>', methods=['DELETE'])
def delete_bill(id):
    """Soft delete a bill"""
    try:
        bill = Bill.objects.get(id=id)
        data = request.get_json() or {}

        bill.is_deleted = True
        bill.deleted_at = datetime.utcnow()
        bill.deletion_reason = data.get('deletion_reason', '')
        bill.updated_at = datetime.utcnow()

        # Restore product stock - only for products from bill's branch
        if bill.branch:
            for item in bill.items:
                if item.item_type == 'product' and item.product:
                    try:
                        item.product.reload()
                        # Verify product belongs to bill's branch before restoring stock
                        if item.product.branch and str(item.product.branch.id) == str(bill.branch.id):
                            item.product.stock_quantity += item.quantity
                            item.product.save()
                    except Exception as e:
                        # Skip products that can't be restored (deleted, etc.)
                        print(f"Warning: Could not restore stock for product {getattr(item.product, 'id', 'unknown')}: {e}")
                        continue

        bill.save()

        # Remove associated cash register entry when bill is deleted
        try:
            CashTransaction.objects(bill_ref=bill).delete()
        except Exception as e:
            print(f"Warning: Could not remove cash transaction for bill {getattr(bill, 'bill_number', 'unknown')}: {e}")

        return jsonify({'message': 'Bill deleted successfully'})
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/deleted', methods=['GET'])
def get_deleted_bills():
    """Get all deleted bills"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Bill.objects.filter(is_deleted=True)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(deleted_at__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end to end of day to include all data from the end date
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(deleted_at__lte=end)

        # Force evaluation by converting to list
        bills = list(query.order_by('-deleted_at'))

        result = []
        for b in bills:
            customer_name = 'Walk-in'
            if b.customer:
                b.customer.reload()
                customer_name = f"{b.customer.first_name} {b.customer.last_name}"
            
            result.append({
                'id': str(b.id),
                'bill_number': b.bill_number,
                'customer_name': customer_name,
                'final_amount': b.final_amount,
                'deleted_at': b.deleted_at.isoformat() if b.deleted_at else None,
                'deletion_reason': b.deletion_reason
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/stats', methods=['GET'])
def get_bill_stats():
    """Get bill statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

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

        total_bills = len(bills)
        total_revenue = sum([b.final_amount for b in bills])
        avg_bill_value = total_revenue / total_bills if total_bills > 0 else 0

        # Payment mode breakdown
        payment_modes = {}
        for bill in bills:
            mode = bill.payment_mode or 'unknown'
            if mode not in payment_modes:
                payment_modes[mode] = {'count': 0, 'amount': 0}
            payment_modes[mode]['count'] += 1
            payment_modes[mode]['amount'] += bill.final_amount

        return jsonify({
            'total_bills': total_bills,
            'total_revenue': total_revenue,
            'average_bill_value': round(avg_bill_value, 2),
            'payment_mode_breakdown': payment_modes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<bill_id>/invoice', methods=['GET'])
@require_auth
def get_invoice_data(bill_id, current_user=None):
    """Get complete invoice data for a bill - OPTIMIZED with batch fetching"""
    try:
        bill = Bill.objects.get(id=bill_id)
        invoice_data = _build_invoice_data(bill)
        return jsonify(invoice_data)
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bill_bp.route('/bills/<bill_id>/invoice/html', methods=['GET'])
@require_auth
def get_invoice_html(bill_id, current_user=None):
    """Get invoice as rendered HTML for viewing - OPTIMIZED with batch fetching"""
    try:
        from services.invoice_pdf_service import render_invoice_html
        bill = Bill.objects.get(id=bill_id)
        invoice_data = _build_invoice_data(bill)
        html_content = render_invoice_html(invoice_data, show_actions=True)
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Bill.DoesNotExist:
        return '<h1>Bill not found</h1>', 404, {'Content-Type': 'text/html'}
    except Exception as e:
        return f'<h1>Error: {str(e)}</h1>', 500, {'Content-Type': 'text/html'}


@bill_bp.route('/bills/<bill_id>/invoice/pdf', methods=['GET'])
@require_auth
def download_invoice_pdf(bill_id, current_user=None):
    """Generate and download invoice as PDF - Uses stored PDF from GridFS if available"""
    try:
        from services.invoice_pdf_service import generate_invoice_pdf
        from services.pdf_storage_service import get_pdf_from_gridfs
        
        bill = Bill.objects.get(id=bill_id)
        
        # Try to retrieve PDF from GridFS - check Invoice first (most reliable), then Bill
        pdf_bytes = None
        pdf_source = None
        invoice_number = bill.bill_number
        
        # First, try Invoice's pdf_file_id (most reliable - stored during checkout)
        try:
            invoice = Invoice.objects(bill=bill).first()
            if invoice and invoice.pdf_file_id:
                try:
                    pdf_bytes = get_pdf_from_gridfs(invoice.pdf_file_id)
                    if pdf_bytes:
                        invoice_number = invoice.invoice_number
                        pdf_source = 'Invoice GridFS'
                        print(f"[DOWNLOAD PDF] Retrieved PDF from Invoice GridFS: file_id={invoice.pdf_file_id}, size={len(pdf_bytes)} bytes")
                        
                        # Update invoice status to downloaded
                        if invoice.status in ['generated', 'viewed']:
                            invoice.status = 'downloaded'
                            invoice.downloaded_at = datetime.utcnow()
                            invoice.save()
                except Exception as e:
                    print(f"[DOWNLOAD PDF] Warning: Failed to retrieve PDF from Invoice GridFS (file_id={invoice.pdf_file_id}): {e}")
        except Exception as e:
            print(f"[DOWNLOAD PDF] Warning: Failed to query Invoice collection: {e}")
        
        # Fallback to Bill's pdf_file_id
        if not pdf_bytes and bill.pdf_file_id:
            try:
                pdf_bytes = get_pdf_from_gridfs(bill.pdf_file_id)
                if pdf_bytes:
                    pdf_source = 'Bill GridFS'
                    print(f"[DOWNLOAD PDF] Retrieved PDF from Bill GridFS: file_id={bill.pdf_file_id}, size={len(pdf_bytes)} bytes")
            except Exception as e:
                print(f"[DOWNLOAD PDF] Warning: Failed to retrieve PDF from Bill GridFS (file_id={bill.pdf_file_id}): {e}")
        
        # Fallback to on-demand generation if PDF not in GridFS
        if not pdf_bytes:
            print(f"[DOWNLOAD PDF] PDF not in GridFS, generating on-demand for bill {bill_id}")
            invoice_data = _build_invoice_data(bill)
            pdf_bytes = generate_invoice_pdf(invoice_data)
            invoice_number = invoice_data.get('invoice_number', bill.bill_number)
            pdf_source = 'On-demand generation'
            print(f"[DOWNLOAD PDF] Generated PDF on-demand, size={len(pdf_bytes)} bytes")

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice_number}.pdf'
        
        # Add caching headers for better performance
        if pdf_source and 'GridFS' in pdf_source:
            # Cache PDFs from GridFS for 1 hour (they don't change)
            response.headers['Cache-Control'] = 'public, max-age=3600'
        else:
            # Don't cache on-demand generated PDFs
            response.headers['Cache-Control'] = 'no-cache'
        
        print(f"[DOWNLOAD PDF] Serving PDF: source={pdf_source}, invoice={invoice_number}")
        return response
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bill_bp.route('/bills/<bill_id>/share-link', methods=['POST'])
@require_auth
def generate_share_link(bill_id, current_user=None):
    """Generate a short shareable link for an invoice"""
    try:
        import secrets

        bill = Bill.objects.get(id=bill_id)

        # Find invoice for this bill
        invoice = Invoice.objects(bill=bill).first()
        if not invoice:
            response = jsonify({'error': 'Invoice not found for this bill'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # Reuse existing share_code if already generated (idempotent)
        if invoice.share_code:
            response = jsonify({'share_code': invoice.share_code})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # Generate a unique 8-char URL-safe code
        for _ in range(5):
            code = secrets.token_urlsafe(6)  # 8 chars
            if not Invoice.objects(share_code=code).first():
                break
        else:
            response = jsonify({'error': 'Failed to generate unique share code'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500

        invoice.share_code = code
        if invoice.status == 'generated':
            invoice.status = 'shared'
        invoice.shared_at = datetime.utcnow()
        invoice.save()
        print(f"[SHARE LINK] Generated share_code={code} for invoice {invoice.invoice_number}")

        response = jsonify({'share_code': code})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Bill.DoesNotExist:
        response = jsonify({'error': 'Bill not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


# Public invoice routes - registered directly on app (not via blueprint) to avoid /api prefix
def public_invoice_view(token):
    """Public invoice view via signed token — no auth required. OPTIMIZED with batch fetching."""
    try:
        import jwt as pyjwt
        from services.invoice_pdf_service import render_invoice_html
        from flask import request

        payload = pyjwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        bill_id = payload['bill_id']
        bill = Bill.objects.get(id=bill_id)
        invoice_data = _build_invoice_data(bill)
        
        # Generate download URL for the PDF
        base_url = request.url_root.rstrip('/')
        download_url = f"{base_url}/invoice/pdf/{token}"
        
        # Show actions (including download button) for public view
        html_content = render_invoice_html(invoice_data, show_actions=True, download_url=download_url)
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

    except Exception as e:
        import jwt as pyjwt
        if isinstance(e, pyjwt.ExpiredSignatureError):
            return '<h1>This invoice link has expired</h1><p>Please request a new link from the salon.</p>', 410, {'Content-Type': 'text/html'}
        if isinstance(e, pyjwt.InvalidTokenError):
            return '<h1>Invalid invoice link</h1><p>This link is not valid.</p>', 400, {'Content-Type': 'text/html'}
        if isinstance(e, Bill.DoesNotExist):
            return '<h1>Invoice not found</h1>', 404, {'Content-Type': 'text/html'}
        return f'<h1>Error loading invoice</h1>', 500, {'Content-Type': 'text/html'}


# Public invoice routes - registered directly on app (not via blueprint) to avoid /api prefix
def public_invoice_pdf(token):
    """Public invoice PDF download via signed token — no auth required. Uses stored PDF from GridFS if available."""
    try:
        import jwt as pyjwt
        from services.invoice_pdf_service import generate_invoice_pdf
        from services.pdf_storage_service import get_pdf_from_gridfs

        payload = pyjwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        bill_id = payload['bill_id']
        bill = Bill.objects.get(id=bill_id)
        
        # Try to retrieve PDF from GridFS - check Invoice first (most reliable), then Bill
        pdf_bytes = None
        pdf_file_id = None
        pdf_source = None
        invoice_number = bill.bill_number
        
        # First, try Invoice's pdf_file_id (most reliable - stored during checkout)
        try:
            invoice = Invoice.objects(bill=bill).first()
            if invoice and invoice.pdf_file_id:
                try:
                    pdf_bytes = get_pdf_from_gridfs(invoice.pdf_file_id)
                    if pdf_bytes:
                        pdf_file_id = invoice.pdf_file_id
                        invoice_number = invoice.invoice_number
                        pdf_source = 'Invoice GridFS'
                        print(f"[PUBLIC PDF] Retrieved PDF from Invoice GridFS: file_id={invoice.pdf_file_id}, size={len(pdf_bytes)} bytes")
                        
                        # Update invoice status to viewed if not already
                        if invoice.status == 'generated':
                            invoice.status = 'viewed'
                            invoice.viewed_at = datetime.utcnow()
                            invoice.save()
                except Exception as e:
                    print(f"[PUBLIC PDF] Warning: Failed to retrieve PDF from Invoice GridFS (file_id={invoice.pdf_file_id}): {e}")
        except Exception as e:
            print(f"[PUBLIC PDF] Warning: Failed to query Invoice collection: {e}")
        
        # Fallback to Bill's pdf_file_id
        if not pdf_bytes and bill.pdf_file_id:
            try:
                pdf_bytes = get_pdf_from_gridfs(bill.pdf_file_id)
                if pdf_bytes:
                    pdf_file_id = bill.pdf_file_id
                    pdf_source = 'Bill GridFS'
                    print(f"[PUBLIC PDF] Retrieved PDF from Bill GridFS: file_id={bill.pdf_file_id}, size={len(pdf_bytes)} bytes")
            except Exception as e:
                print(f"[PUBLIC PDF] Warning: Failed to retrieve PDF from Bill GridFS (file_id={bill.pdf_file_id}): {e}")
        
        # Fallback to on-demand generation if PDF not in GridFS
        if not pdf_bytes:
            print(f"[PUBLIC PDF] PDF not in GridFS, generating on-demand for bill {bill_id}")
            invoice_data = _build_invoice_data(bill)
            pdf_bytes = generate_invoice_pdf(invoice_data)
            invoice_number = invoice_data.get('invoice_number', bill.bill_number)
            pdf_source = 'On-demand generation'
            print(f"[PUBLIC PDF] Generated PDF on-demand, size={len(pdf_bytes)} bytes")

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        
        # Use 'attachment' for mobile devices (better download behavior), 'inline' for desktop (better UX)
        disposition = 'attachment' if is_mobile_device() else 'inline'
        response.headers['Content-Disposition'] = f'{disposition}; filename=invoice_{invoice_number}.pdf'
        
        # Add caching headers for better performance
        if pdf_source and 'GridFS' in pdf_source:
            # Cache PDFs from GridFS for 1 hour (they don't change)
            response.headers['Cache-Control'] = 'public, max-age=3600'
        else:
            # Don't cache on-demand generated PDFs
            response.headers['Cache-Control'] = 'no-cache'
        
        print(f"[PUBLIC PDF] Serving PDF: source={pdf_source}, invoice={invoice_number}, disposition={disposition}")
        return response

    except Exception as e:
        import jwt as pyjwt
        if isinstance(e, pyjwt.ExpiredSignatureError):
            return '<h1>This invoice link has expired</h1><p>Please request a new link from the salon.</p>', 410, {'Content-Type': 'text/html'}
        if isinstance(e, pyjwt.InvalidTokenError):
            return '<h1>Invalid invoice link</h1><p>This link is not valid.</p>', 400, {'Content-Type': 'text/html'}
        if isinstance(e, Bill.DoesNotExist):
            return '<h1>Invoice not found</h1>', 404, {'Content-Type': 'text/html'}
        return f'<h1>Error generating PDF</h1>', 500, {'Content-Type': 'text/html'}


# Public invoice routes - registered directly on app (not via blueprint) to avoid /api prefix
def short_invoice_view(share_code):
    """Public invoice view via short share code — no auth required."""
    try:
        from services.invoice_pdf_service import render_invoice_html
        from flask import request

        invoice = Invoice.objects(share_code=share_code).first()
        if not invoice:
            return '<h1>Invoice not found</h1><p>This link is not valid.</p>', 404, {'Content-Type': 'text/html'}

        # Invoice links remain accessible permanently unless manually deleted
        bill = invoice.bill
        invoice_data = _build_invoice_data(bill)
        
        # Generate download URL for the PDF
        base_url = request.url_root.rstrip('/')
        download_url = f"{base_url}/i/{share_code}/pdf"
        
        # Show actions (including download button) for public view
        html_content = render_invoice_html(invoice_data, show_actions=True, download_url=download_url)

        # Track view
        if invoice.status in ('generated', 'shared'):
            invoice.status = 'viewed'
            invoice.viewed_at = datetime.utcnow()
            invoice.save()

        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        print(f"[SHORT LINK] Error viewing invoice: {e}")
        return '<h1>Error loading invoice</h1>', 500, {'Content-Type': 'text/html'}


# Public invoice routes - registered directly on app (not via blueprint) to avoid /api prefix
def short_invoice_pdf(share_code):
    """Public invoice PDF download via short share code — no auth required."""
    try:
        from services.invoice_pdf_service import generate_invoice_pdf
        from services.pdf_storage_service import get_pdf_from_gridfs

        invoice = Invoice.objects(share_code=share_code).first()
        if not invoice:
            return '<h1>Invoice not found</h1><p>This link is not valid.</p>', 404, {'Content-Type': 'text/html'}

        # Invoice links remain accessible permanently unless manually deleted
        bill = invoice.bill
        invoice_number = invoice.invoice_number

        # Try to retrieve stored PDF from GridFS with better error handling
        pdf_bytes = None
        pdf_source = None
        
        # First, try Invoice's pdf_file_id (most reliable - stored during checkout)
        if invoice.pdf_file_id:
            try:
                pdf_bytes = get_pdf_from_gridfs(invoice.pdf_file_id)
                if pdf_bytes:
                    pdf_source = 'Invoice GridFS'
                    print(f"[SHORT PDF] Retrieved PDF from Invoice GridFS: file_id={invoice.pdf_file_id}, size={len(pdf_bytes)} bytes")
            except Exception as e:
                print(f"[SHORT PDF] Warning: Failed to retrieve PDF from Invoice GridFS (file_id={invoice.pdf_file_id}): {e}")
        
        # Fallback to Bill's pdf_file_id
        if not pdf_bytes and bill.pdf_file_id:
            try:
                pdf_bytes = get_pdf_from_gridfs(bill.pdf_file_id)
                if pdf_bytes:
                    pdf_source = 'Bill GridFS'
                    print(f"[SHORT PDF] Retrieved PDF from Bill GridFS: file_id={bill.pdf_file_id}, size={len(pdf_bytes)} bytes")
            except Exception as e:
                print(f"[SHORT PDF] Warning: Failed to retrieve PDF from Bill GridFS (file_id={bill.pdf_file_id}): {e}")

        # Fallback to on-demand generation (slow but works)
        if not pdf_bytes:
            print(f"[SHORT PDF] PDF not in GridFS, generating on-demand for invoice {invoice.invoice_number}")
            invoice_data = _build_invoice_data(bill)
            pdf_bytes = generate_invoice_pdf(invoice_data)
            invoice_number = invoice_data.get('invoice_number', bill.bill_number)
            pdf_source = 'On-demand generation'
            print(f"[SHORT PDF] Generated PDF on-demand, size={len(pdf_bytes)} bytes")

        # Track download
        if invoice.status in ('generated', 'shared', 'viewed'):
            invoice.status = 'downloaded'
            invoice.downloaded_at = datetime.utcnow()
            invoice.save()

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        
        # Use 'attachment' for mobile devices (better download behavior), 'inline' for desktop (better UX)
        disposition = 'attachment' if is_mobile_device() else 'inline'
        response.headers['Content-Disposition'] = f'{disposition}; filename=invoice_{invoice_number}.pdf'
        
        # Add caching headers for better performance
        if pdf_source and 'GridFS' in pdf_source:
            # Cache PDFs from GridFS for 1 hour (they don't change)
            response.headers['Cache-Control'] = 'public, max-age=3600'
        else:
            # Don't cache on-demand generated PDFs
            response.headers['Cache-Control'] = 'no-cache'
        
        print(f"[SHORT PDF] Serving PDF: source={pdf_source}, invoice={invoice_number}, disposition={disposition}")
        return response
    except Exception as e:
        print(f"[SHORT LINK] Error serving PDF: {e}")
        import traceback
        traceback.print_exc()
        return '<h1>Error generating PDF</h1>', 500, {'Content-Type': 'text/html'}


@bill_bp.route('/invoices', methods=['GET'])
@require_auth
def get_invoices(current_user=None):
    """Get all invoices with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        branch_id = request.args.get('branch_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Build query
        query = Invoice.objects
        
        # Apply filters
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                query = query.filter(customer=customer)
            except Customer.DoesNotExist:
                pass
        
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id)
                query = query.filter(branch=branch)
            except Branch.DoesNotExist:
                pass
        else:
            # Filter by user's selected branch if no branch_id provided
            branch = get_selected_branch(request, current_user)
            if branch:
                query = query.filter(branch=branch)
        
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                query = query.filter(generated_at__gte=start)
            if end:
                query = query.filter(generated_at__lte=end)
        
        if status:
            query = query.filter(status=status)
        
        # Get count and paginate
        total = query.count()
        invoices = list(query.order_by('-generated_at').skip((page - 1) * per_page).limit(per_page))
        
        result = []
        for inv in invoices:
            result.append({
                'id': str(inv.id),
                'invoice_number': inv.invoice_number,
                'bill_id': str(inv.bill.id) if inv.bill else None,
                'bill_number': inv.bill.bill_number if inv.bill else None,
                'customer_id': str(inv.customer.id) if inv.customer else None,
                'customer_name': f"{inv.customer.first_name or ''} {inv.customer.last_name or ''}".strip() if inv.customer else 'Walk-in',
                'branch_id': str(inv.branch.id) if inv.branch else None,
                'branch_name': inv.branch.name if inv.branch else None,
                'pdf_file_id': str(inv.pdf_file_id) if inv.pdf_file_id else None,
                'status': inv.status,
                'generated_at': inv.generated_at.isoformat() if inv.generated_at else None,
                'shared_at': inv.shared_at.isoformat() if inv.shared_at else None,
                'viewed_at': inv.viewed_at.isoformat() if inv.viewed_at else None,
                'downloaded_at': inv.downloaded_at.isoformat() if inv.downloaded_at else None,
                'total': inv.invoice_data.get('summary', {}).get('total', 0) if inv.invoice_data else 0
            })
        
        return jsonify({
            'invoices': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bill_bp.route('/invoices/<id>', methods=['GET'])
@require_auth
def get_invoice(id, current_user=None):
    """Get a specific invoice by ID"""
    try:
        invoice = Invoice.objects.get(id=id)
        
        return jsonify({
            'id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'bill_id': str(invoice.bill.id) if invoice.bill else None,
            'bill_number': invoice.bill.bill_number if invoice.bill else None,
            'customer_id': str(invoice.customer.id) if invoice.customer else None,
            'customer_name': f"{invoice.customer.first_name or ''} {invoice.customer.last_name or ''}".strip() if invoice.customer else 'Walk-in',
            'branch_id': str(invoice.branch.id) if invoice.branch else None,
            'branch_name': invoice.branch.name if invoice.branch else None,
            'pdf_file_id': str(invoice.pdf_file_id) if invoice.pdf_file_id else None,
            'invoice_data': invoice.invoice_data,
            'status': invoice.status,
            'generated_at': invoice.generated_at.isoformat() if invoice.generated_at else None,
            'shared_at': invoice.shared_at.isoformat() if invoice.shared_at else None,
            'viewed_at': invoice.viewed_at.isoformat() if invoice.viewed_at else None,
            'downloaded_at': invoice.downloaded_at.isoformat() if invoice.downloaded_at else None,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None
        })
    except Invoice.DoesNotExist:
        return jsonify({'error': 'Invoice not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bill_bp.route('/invoices/bill/<bill_id>', methods=['GET'])
@require_auth
def get_invoice_by_bill(bill_id, current_user=None):
    """Get invoice by bill ID"""
    try:
        bill = Bill.objects.get(id=bill_id)
        invoice = Invoice.objects(bill=bill).first()
        
        if not invoice:
            return jsonify({'error': 'Invoice not found for this bill'}), 404
        
        return jsonify({
            'id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'bill_id': str(invoice.bill.id) if invoice.bill else None,
            'bill_number': invoice.bill.bill_number if invoice.bill else None,
            'customer_id': str(invoice.customer.id) if invoice.customer else None,
            'customer_name': f"{invoice.customer.first_name or ''} {invoice.customer.last_name or ''}".strip() if invoice.customer else 'Walk-in',
            'branch_id': str(invoice.branch.id) if invoice.branch else None,
            'branch_name': invoice.branch.name if invoice.branch else None,
            'pdf_file_id': str(invoice.pdf_file_id) if invoice.pdf_file_id else None,
            'invoice_data': invoice.invoice_data,
            'status': invoice.status,
            'generated_at': invoice.generated_at.isoformat() if invoice.generated_at else None,
            'shared_at': invoice.shared_at.isoformat() if invoice.shared_at else None,
            'viewed_at': invoice.viewed_at.isoformat() if invoice.viewed_at else None,
            'downloaded_at': invoice.downloaded_at.isoformat() if invoice.downloaded_at else None
        })
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bill_bp.route('/invoices/customer/<customer_id>', methods=['GET'])
@require_auth
def get_customer_invoices(customer_id, current_user=None):
    """Get all invoices for a specific customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        query = Invoice.objects.filter(customer=customer)
        
        # Get count and paginate
        total = query.count()
        invoices = list(query.order_by('-generated_at').skip((page - 1) * per_page).limit(per_page))
        
        result = []
        for inv in invoices:
            result.append({
                'id': str(inv.id),
                'invoice_number': inv.invoice_number,
                'bill_id': str(inv.bill.id) if inv.bill else None,
                'bill_number': inv.bill.bill_number if inv.bill else None,
                'branch_id': str(inv.branch.id) if inv.branch else None,
                'branch_name': inv.branch.name if inv.branch else None,
                'pdf_file_id': str(inv.pdf_file_id) if inv.pdf_file_id else None,
                'status': inv.status,
                'generated_at': inv.generated_at.isoformat() if inv.generated_at else None,
                'total': inv.invoice_data.get('summary', {}).get('total', 0) if inv.invoice_data else 0
            })
        
        return jsonify({
            'invoices': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        })
    except Customer.DoesNotExist:
        return jsonify({'error': 'Customer not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
