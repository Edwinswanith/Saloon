from flask import Blueprint, request, jsonify
from models import Bill, Customer, Product, PrepaidPackage, LoyaltyProgramSettings, BillItemEmbedded
from datetime import datetime
from bson import ObjectId
from mongoengine import Q
import uuid

bill_bp = Blueprint('bill', __name__)

def generate_bill_number():
    """Generate unique bill number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4().hex[:4]).upper()
    return f"BILL-{timestamp}-{random_suffix}"

@bill_bp.route('/bills', methods=['GET'])
def get_bills():
    """Get all bills with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        payment_mode = request.args.get('payment_mode')
        booking_status = request.args.get('booking_status')
        include_deleted = request.args.get('include_deleted', type=bool, default=False)

        query = Bill.objects

        # Apply filters
        if not include_deleted:
            query = query.filter(is_deleted=False)
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                query = query.filter(customer=customer)
            except Customer.DoesNotExist:
                pass
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(bill_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(bill_date__lte=end)
        if payment_mode:
            query = query.filter(payment_mode=payment_mode)
        if booking_status:
            query = query.filter(booking_status=booking_status)

        bills = query.order_by('-bill_date')

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
    """Create a new bill (draft)"""
    try:
        data = request.get_json()

        customer = None
        if data.get('customer_id'):
            try:
                customer = Customer.objects.get(id=data['customer_id'])
            except Customer.DoesNotExist:
                pass

        bill = Bill(
            bill_number=generate_bill_number(),
            customer=customer,
            bill_date=datetime.utcnow(),
            subtotal=0,
            discount_amount=0,
            tax_amount=0,
            final_amount=0,
            booking_status=data.get('booking_status', 'service-completed'),
            booking_note=data.get('booking_note'),
            items=[]
        )
        bill.save()

        return jsonify({
            'id': str(bill.id),
            'message': 'Bill created successfully',
            'data': {
                'id': str(bill.id),
                'bill_number': bill.bill_number
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

        if not bill.items:
            bill.items = []
        bill.items.append(item)
        bill.save()

        return jsonify({
            'id': len(bill.items) - 1,  # Return index
            'message': 'Item added to bill successfully'
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

        # Calculate subtotal from items
        subtotal = sum([float(item.total) if item.total else 0.0 for item in bill.items])
        subtotal = float(subtotal) if subtotal else 0.0

        # Get discount
        discount_amount = float(data.get('discount_amount', 0) or 0)
        discount_type = data.get('discount_type', 'fix')

        if discount_type == 'percentage':
            discount_amount = float(subtotal) * (float(discount_amount) / 100.0)

        # Calculate tax
        tax_rate = float(data.get('tax_rate', 0) or 0)
        amount_after_discount = float(subtotal) - float(discount_amount)
        tax_amount = float(amount_after_discount) * (float(tax_rate) / 100.0)

        # Calculate final amount
        final_amount = amount_after_discount + tax_amount

        # Update bill
        bill.subtotal = subtotal
        bill.discount_amount = discount_amount
        bill.discount_type = discount_type
        bill.tax_amount = tax_amount
        bill.tax_rate = tax_rate
        bill.final_amount = final_amount
        bill.payment_mode = data['payment_mode']
        bill.booking_status = data.get('booking_status', 'service-completed')
        bill.updated_at = datetime.utcnow()

        # Process payment
        if data['payment_mode'] == 'wallet' and bill.customer:
            bill.customer.reload()
            if bill.customer.wallet_balance < final_amount:
                return jsonify({'error': 'Insufficient wallet balance'}), 400
            bill.customer.wallet_balance -= final_amount
            bill.customer.save()

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

        # Update product stock
        for item in bill.items:
            if item.item_type == 'product' and item.product:
                item.product.reload()
                item.product.stock_quantity -= item.quantity
                if item.product.stock_quantity < 0:
                    return jsonify({'error': f'Insufficient stock for product: {item.product.name}'}), 400
                item.product.save()

        # Update customer loyalty points
        if bill.customer:
            bill.customer.reload()
            loyalty_settings = LoyaltyProgramSettings.get_settings()
            if loyalty_settings.enabled and loyalty_settings.earning_rate:
                earning_rate = float(loyalty_settings.earning_rate) if loyalty_settings.earning_rate else 0.0
                if earning_rate > 0:
                    points_earned = int(float(final_amount) / float(earning_rate))
                    bill.customer.loyalty_points += points_earned
                    bill.customer.save()

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

        # Restore wallet balance
        if bill.payment_mode == 'wallet' and bill.customer:
            bill.customer.reload()
            bill.customer.wallet_balance += bill.final_amount
            bill.customer.save()

        # Restore loyalty points
        if bill.customer:
            bill.customer.reload()
            bill.customer.loyalty_points -= int(bill.final_amount)
            if bill.customer.loyalty_points < 0:
                bill.customer.loyalty_points = 0
            bill.customer.save()

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
            query = query.filter(deleted_at__lte=end)

        bills = query.order_by('-deleted_at')

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
            query = query.filter(bill_date__lte=end)

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
