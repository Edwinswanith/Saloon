from flask import Blueprint, request, jsonify, make_response
from models import Bill, Customer, Product, PrepaidPackage, BillItemEmbedded, DiscountApprovalRequest, Staff, Membership, Branch
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from mongoengine import Q
from utils.auth import get_current_user, require_auth
from utils.branch_filter import get_selected_branch
from utils.date_utils import get_ist_date_range
import uuid

# Discount limits by role - Only owner can apply discounts
DISCOUNT_LIMITS = {
    'staff': 0,      # No discount access
    'manager': 0,   # No discount access
    'owner': 100    # Unlimited (only owner)
}

bill_bp = Blueprint('bill', __name__)

def generate_bill_number():
    """Generate unique bill number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4().hex[:4]).upper()
    return f"BILL-{timestamp}-{random_suffix}"

def generate_invoice_number():
    """Generate sequential invoice number in format INV-000400"""
    try:
        # Get the last invoice number from bills
        last_bill = Bill.objects.order_by('-created_at').first()
        
        if last_bill and last_bill.bill_number:
            # Try to extract invoice number from bill_number or use a counter
            # For now, we'll use a simple counter based on total bills
            total_bills = Bill.objects.count()
            invoice_num = total_bills + 1
        else:
            invoice_num = 1
        
        # Format as INV-000400 (6-digit zero-padded)
        return f"INV-{invoice_num:06d}"
    except Exception as e:
        # Fallback to timestamp-based if error occurs
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"INV-{timestamp[:6]}"

def resolve_bill_branch(current_user=None, appointment=None, customer=None):
    """Best-effort branch resolution for bills."""
    if appointment and getattr(appointment, 'branch', None):
        return appointment.branch
    if customer and getattr(customer, 'branch', None):
        return customer.branch

    branch = None
    if current_user:
        branch = get_selected_branch(request, current_user)
    if not branch:
        branch_id_header = request.headers.get('X-Branch-Id')
        if branch_id_header and ObjectId.is_valid(branch_id_header):
            branch = Branch.objects(id=branch_id_header).first()
    return branch

@bill_bp.route('/bills', methods=['GET'])
@require_auth
def get_bills(current_user=None):
    """Get all bills with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        payment_mode = request.args.get('payment_mode')
        booking_status = request.args.get('booking_status')
        include_deleted = request.args.get('include_deleted', type=bool, default=False)

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

        # Force evaluation by converting to list
        bills = list(query.order_by('-bill_date'))

        result = []
        for b in bills:
            try:
                customer_name = 'Walk-in'
                customer_mobile = None
                customer_obj_id = None
                if b.customer:
                    try:
                        b.customer.reload()  # Ensure customer is fetched
                    except:
                        pass  # Customer might be deleted, continue with cached data
                    customer_name = f"{b.customer.first_name} {b.customer.last_name}"
                    customer_mobile = b.customer.mobile
                    customer_obj_id = str(b.customer.id)
                
                result.append({
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
                    'is_deleted': b.is_deleted,
                    'created_at': b.created_at.isoformat() if b.created_at else None
                })
            except Exception as e:
                print(f"Error processing bill {b.id}: {e}")
                continue

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<id>', methods=['GET'])
def get_bill(id):
    """Get a single bill with items"""
    try:
        bill = Bill.objects.get(id=id)
        
        customer_name = 'Walk-in'
        customer_mobile = None
        customer_obj_id = None
        if bill.customer:
            try:
                bill.customer.reload()
            except:
                pass  # Continue with cached customer data
            customer_name = f"{bill.customer.first_name} {bill.customer.last_name}"
            customer_mobile = bill.customer.mobile
            customer_obj_id = str(bill.customer.id)

        items = []
        for idx, item in enumerate(bill.items):
            item_data = {
                'id': idx,  # Index as ID for embedded documents
                'item_type': item.item_type,
                'service_id': str(item.service.id) if item.service else None,
                'service_name': item.service.name if item.service and hasattr(item.service, 'name') else None,
                'package_id': str(item.package.id) if item.package else None,
                'package_name': item.package.name if item.package and hasattr(item.package, 'name') else None,
                'product_id': str(item.product.id) if item.product else None,
                'product_name': item.product.name if item.product and hasattr(item.product, 'name') else None,
                'staff_id': str(item.staff.id) if item.staff else None,
                'staff_name': f"{item.staff.first_name} {item.staff.last_name}" if item.staff and hasattr(item.staff, 'first_name') else None,
                'start_time': item.start_time if item.start_time else None,  # Already a string
                'price': item.price,
                'discount': item.discount,
                'quantity': item.quantity,
                'total': item.total
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
        
        # If existing unchecked-out bill found, return it
        if existing_bill:
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
                pass

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
        prepaid = None
        membership = None
        staff = None

        from models import Service, Package, PrepaidPackage as Prepaid, Membership, Staff as StaffModel
        if data.get('service_id'):
            try:
                service = Service.objects.get(id=data['service_id'])
            except:
                pass
        if data.get('package_id'):
            try:
                package = Package.objects.get(id=data['package_id'])
            except:
                pass
        if data.get('product_id'):
            try:
                product = Product.objects.get(id=data['product_id'])
            except:
                pass
        if data.get('prepaid_id'):
            try:
                prepaid = Prepaid.objects.get(id=data['prepaid_id'])
            except:
                pass
        if data.get('membership_id'):
            try:
                membership = Membership.objects.get(id=data['membership_id'])
            except:
                pass
        if data.get('staff_id'):
            try:
                staff = StaffModel.objects.get(id=data['staff_id'])
            except:
                pass

        item = BillItemEmbedded(
            item_type=data['item_type'],
            service=service,
            package=package,
            product=product,
            prepaid=prepaid,
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

        if not bill.items:
            bill.items = []
        bill.items.append(item)
        bill.save()

        return jsonify({
            'id': len(bill.items) - 1,  # Return index
            'message': 'Item added to bill successfully',
            'product_stock_validated': product is not None
        }), 201
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
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
def checkout_bill(id):
    """Complete checkout process for a bill"""
    try:
        bill = Bill.objects.get(id=id)
        data = request.get_json()

        # Check if bill is already checked out to prevent double stock reduction
        is_already_checked_out = (bill.booking_status == 'service-completed' and bill.payment_mode)

        # Get current user and check permissions
        current_user = get_current_user()
        user_role = current_user.get('role') if current_user else 'staff'
        
        # Calculate subtotal from items
        subtotal = sum([float(item.total) if item.total else 0.0 for item in bill.items])
        subtotal = float(subtotal) if subtotal else 0.0

        # Check for active membership discount first (automatic, cannot be overridden)
        membership_discount_applied = False
        discount_amount = 0.0
        discount_type = 'fix'
        
        if bill.customer:
            # Get customer's active membership
            active_membership = Membership.objects(
                customer=bill.customer,
                status='active',
                expiry_date__gte=datetime.utcnow()
            ).first()
            
            if active_membership and active_membership.plan and active_membership.plan.allocated_discount > 0:
                # Apply membership discount automatically
                membership_discount_percent = float(active_membership.plan.allocated_discount)
                discount_amount = float(subtotal) * (membership_discount_percent / 100.0)
                discount_type = 'membership'
                membership_discount_applied = True
        
        # If no membership discount, check for manual discount (owner only)
        if not membership_discount_applied:
            # Get discount from request
            discount_amount = float(data.get('discount_amount', 0) or 0)
            discount_type = data.get('discount_type', 'fix')
            
            # SECURITY: Only owners can apply manual discounts
            if discount_amount > 0 and user_role != 'owner':
                response = jsonify({
                    'error': 'Insufficient permissions',
                    'message': 'Only owners can apply discounts. Please contact the owner to apply a discount.'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 403
            
            # Calculate discount percentage for manual discounts
            if discount_type == 'percentage':
                discount_percent = float(discount_amount)
                discount_amount = float(subtotal) * (float(discount_amount) / 100.0)
            elif discount_amount > 0 and subtotal > 0:
                discount_percent = (discount_amount / subtotal) * 100
        
        # Owners don't need approval - they have unlimited discount access
        needs_approval = False
        
        # No approval needed for owners - they have full discount access

        # Calculate tax on amount after membership discount
        tax_rate = float(data.get('tax_rate', 0) or 0)
        amount_after_all_discounts = float(subtotal) - float(discount_amount)
        if amount_after_all_discounts < 0:
            amount_after_all_discounts = 0.0
        tax_amount = float(amount_after_all_discounts) * (float(tax_rate) / 100.0)

        # Calculate final amount
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

        if not bill.branch:
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

        # Update bill
        bill.subtotal = subtotal
        bill.discount_amount = discount_amount
        bill.discount_type = discount_type
        bill.tax_amount = tax_amount
        bill.tax_rate = tax_rate
        bill.final_amount = final_amount
        bill.payment_mode = data['payment_mode']
        # Always set to 'service-completed' when checkout happens to mark as paid
        bill.booking_status = 'service-completed'
        bill.discount_approval_status = 'none'  # Owners don't need approval
        bill.updated_at = datetime.utcnow()

        # Handle prepaid package payment
        if 'prepaid_package_id' in data and data['prepaid_package_id']:
            try:
                prepaid_package = PrepaidPackage.objects.get(id=data['prepaid_package_id'])
                if prepaid_package.remaining_balance < final_amount:
                    return jsonify({'error': 'Insufficient prepaid balance'}), 400
                prepaid_package.remaining_balance -= final_amount
                if prepaid_package.remaining_balance <= 0:
                    prepaid_package.status = 'used'
                prepaid_package.save()
            except PrepaidPackage.DoesNotExist:
                pass

        # Update product stock - validate and reduce for all products in bill
        # Skip if bill is already checked out to prevent double stock reduction
        if not is_already_checked_out:
            products_to_update = []
            for item in bill.items:
                if item.item_type == 'product' and item.product:
                    # Reload product to get latest stock count (handles concurrent checkouts)
                    item.product.reload()
                    quantity_needed = int(item.quantity) if item.quantity else 1
                    
                    # Validate stock availability before reducing
                    if item.product.stock_quantity is not None:
                        if item.product.stock_quantity < quantity_needed:
                            return jsonify({
                                'error': f'Insufficient stock for product: {item.product.name}. Available: {item.product.stock_quantity}, Required: {quantity_needed}'
                            }), 400
                        
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

        return jsonify({
            'message': 'Checkout completed successfully',
            'bill_number': bill.bill_number,
            'final_amount': bill.final_amount
        })
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

        # Restore product stock
        for item in bill.items:
            if item.item_type == 'product' and item.product:
                item.product.reload()
                item.product.stock_quantity += item.quantity
                item.product.save()

        bill.save()

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
    """Get complete invoice data for a bill"""
    try:
        bill = Bill.objects.get(id=bill_id)
        
        # Get customer data
        customer_data = {
            'id': None,
            'name': 'Walk-in',
            'mobile': None
        }
        if bill.customer:
            try:
                bill.customer.reload()
                customer_data = {
                    'id': str(bill.customer.id),
                    'name': f"{bill.customer.first_name or ''} {bill.customer.last_name or ''}".strip(),
                    'mobile': bill.customer.mobile
                }
            except:
                pass
        
        # Get branch data
        branch_data = {
            'name': 'Saloon',
            'address': '',
            'city': '',
            'phone': '',
            'gstin': ''
        }
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
            except:
                pass
        
        # Get bill items with full details
        items = []
        for idx, item in enumerate(bill.items or []):
            item_name = 'Item'
            item_type = item.item_type or 'service'
            
            # Get item name based on type
            if item.item_type == 'service' and item.service:
                try:
                    item.service.reload()
                    item_name = item.service.name if hasattr(item.service, 'name') else 'Service'
                except:
                    item_name = 'Service'
            elif item.item_type == 'product' and item.product:
                try:
                    item.product.reload()
                    item_name = item.product.name if hasattr(item.product, 'name') else 'Product'
                except:
                    item_name = 'Product'
            elif item.item_type == 'package' and item.package:
                try:
                    item.package.reload()
                    item_name = item.package.name if hasattr(item.package, 'name') else 'Package'
                except:
                    item_name = 'Package'
            
            # Get staff name
            staff_name = 'N/A'
            if item.staff:
                try:
                    item.staff.reload()
                    staff_name = f"{item.staff.first_name or ''} {item.staff.last_name or ''}".strip() if hasattr(item.staff, 'first_name') else 'N/A'
                except:
                    staff_name = 'N/A'
            
            # Calculate tax per item (proportional)
            item_tax = 0.0
            if bill.tax_amount and bill.subtotal:
                item_tax = (float(item.total) / float(bill.subtotal)) * float(bill.tax_amount) if bill.subtotal > 0 else 0.0
            
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
        
        # Generate or retrieve invoice number
        # Try to get from bill_number or generate sequential
        invoice_number = getattr(bill, 'invoice_number', None)
        if not invoice_number:
            # Generate sequential invoice number based on bill creation order
            try:
                # Count bills created before this one (by created_at)
                bills_before = Bill.objects(created_at__lt=bill.created_at).count()
                invoice_num = bills_before + 1
                invoice_number = f"INV-{invoice_num:06d}"
            except:
                # Fallback: use bill_number or generate
                if bill.bill_number.startswith('BILL-'):
                    parts = bill.bill_number.split('-')
                    if len(parts) >= 2:
                        try:
                            # Try to extract a number from the timestamp
                            num_part = parts[1] if len(parts) > 1 else '000001'
                            # Use last 6 digits or generate sequential
                            invoice_num = int(num_part[-6:]) if num_part[-6:].isdigit() else 1
                            invoice_number = f"INV-{invoice_num:06d}"
                        except:
                            invoice_number = generate_invoice_number()
                else:
                    invoice_number = generate_invoice_number()
        
        # Format bill date for display as "Day, DD Mon, YYYY, HH:MM am/pm"
        bill_date = bill.bill_date
        booking_date_str = 'N/A'
        booking_time_str = 'N/A'
        
        if bill_date:
            # Format date as "Tue, 06 Jan, 2026"
            booking_date_str = bill_date.strftime('%a, %d %b, %Y')
            
            # Get first item's start time if available, otherwise use bill_date time
            if items and items[0].get('start_time'):
                try:
                    time_parts = items[0]['start_time'].split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        from datetime import time as dt_time
                        time_obj = dt_time(hour, minute)
                        booking_time_str = time_obj.strftime('%I:%M %p').lower()
                except:
                    # Fallback to bill_date time
                    booking_time_str = bill_date.strftime('%I:%M %p').lower()
            else:
                # Use bill_date time
                booking_time_str = bill_date.strftime('%I:%M %p').lower()
        
        invoice_data = {
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
                'net': float(bill.subtotal) - float(bill.discount_amount) if bill.subtotal else 0.0,
                'tax': float(bill.tax_amount) if bill.tax_amount else 0.0,
                'tax_rate': float(bill.tax_rate) if bill.tax_rate else 0.0,
                'total': float(bill.final_amount) if bill.final_amount else 0.0
            },
            'payment': {
                'status': 'paid' if (bill.booking_status == 'service-completed' 
                                    and bill.payment_mode 
                                    and bill.final_amount > 0) else 'pending',
                'mode': bill.payment_mode or 'cash',
                'source': f"{bill.payment_mode or 'Cash'}: ₹{bill.final_amount or 0}" if (bill.payment_mode and bill.final_amount > 0) else 'Not paid'
            }
        }
        
        return jsonify(invoice_data)
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bill_bp.route('/bills/<bill_id>/invoice/pdf', methods=['GET'])
@require_auth
def download_invoice_pdf(bill_id, current_user=None):
    """Generate and download invoice as PDF"""
    try:
        from services.invoice_pdf_service import generate_invoice_pdf
        
        # Get invoice data
        bill = Bill.objects.get(id=bill_id)
        
        # Get customer data
        customer_data = {
            'id': None,
            'name': 'Walk-in',
            'mobile': None
        }
        if bill.customer:
            try:
                bill.customer.reload()
                customer_data = {
                    'id': str(bill.customer.id),
                    'name': f"{bill.customer.first_name or ''} {bill.customer.last_name or ''}".strip(),
                    'mobile': bill.customer.mobile
                }
            except:
                pass
        
        # Get branch data
        branch_data = {
            'name': 'Saloon',
            'address': '',
            'city': '',
            'phone': '',
            'gstin': ''
        }
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
            except:
                pass
        
        # Get bill items
        items = []
        for idx, item in enumerate(bill.items or []):
            item_name = 'Item'
            item_type = item.item_type or 'service'
            
            if item.item_type == 'service' and item.service:
                try:
                    item.service.reload()
                    item_name = item.service.name if hasattr(item.service, 'name') else 'Service'
                except:
                    item_name = 'Service'
            elif item.item_type == 'product' and item.product:
                try:
                    item.product.reload()
                    item_name = item.product.name if hasattr(item.product, 'name') else 'Product'
                except:
                    item_name = 'Product'
            elif item.item_type == 'package' and item.package:
                try:
                    item.package.reload()
                    item_name = item.package.name if hasattr(item.package, 'name') else 'Package'
                except:
                    item_name = 'Package'
            
            staff_name = 'N/A'
            if item.staff:
                try:
                    item.staff.reload()
                    staff_name = f"{item.staff.first_name or ''} {item.staff.last_name or ''}".strip() if hasattr(item.staff, 'first_name') else 'N/A'
                except:
                    staff_name = 'N/A'
            
            item_tax = 0.0
            if bill.tax_amount and bill.subtotal:
                item_tax = (float(item.total) / float(bill.subtotal)) * float(bill.tax_amount) if bill.subtotal > 0 else 0.0
            
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
        
        # Generate or retrieve invoice number (same logic as get_invoice_data)
        invoice_number = getattr(bill, 'invoice_number', None)
        if not invoice_number:
            try:
                bills_before = Bill.objects(created_at__lt=bill.created_at).count()
                invoice_num = bills_before + 1
                invoice_number = f"INV-{invoice_num:06d}"
            except:
                if bill.bill_number.startswith('BILL-'):
                    parts = bill.bill_number.split('-')
                    if len(parts) >= 2:
                        try:
                            num_part = parts[1] if len(parts) > 1 else '000001'
                            invoice_num = int(num_part[-6:]) if num_part[-6:].isdigit() else 1
                            invoice_number = f"INV-{invoice_num:06d}"
                        except:
                            invoice_number = generate_invoice_number()
                else:
                    invoice_number = generate_invoice_number()
        
        bill_date = bill.bill_date
        booking_date_str = bill_date.strftime('%a, %d %b, %Y') if bill_date else 'N/A'
        booking_time_str = bill_date.strftime('%I:%M %p') if bill_date else 'N/A'
        
        if items and items[0].get('start_time'):
            try:
                time_parts = items[0]['start_time'].split(':')
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    from datetime import time as dt_time
                    time_obj = dt_time(hour, minute)
                    booking_time_str = time_obj.strftime('%I:%M %p')
            except:
                pass
        
        invoice_data = {
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
                'net': float(bill.subtotal) - float(bill.discount_amount) if bill.subtotal else 0.0,
                'tax': float(bill.tax_amount) if bill.tax_amount else 0.0,
                'tax_rate': float(bill.tax_rate) if bill.tax_rate else 0.0,
                'total': float(bill.final_amount) if bill.final_amount else 0.0
            },
            'payment': {
                'status': 'paid' if (bill.booking_status == 'service-completed' 
                                    and bill.payment_mode 
                                    and bill.final_amount > 0) else 'pending',
                'mode': bill.payment_mode or 'cash',
                'source': f"{bill.payment_mode or 'Cash'}: ₹{bill.final_amount or 0}" if (bill.payment_mode and bill.final_amount > 0) else 'Not paid'
            }
        }
        
        # Generate PDF
        pdf_bytes = generate_invoice_pdf(invoice_data)
        
        # Create response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice_number}.pdf'
        
        return response
    except Bill.DoesNotExist:
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
