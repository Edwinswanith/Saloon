from mongoengine import connect, Document, ReferenceField, StringField, IntField, FloatField, DateTimeField, BooleanField, DateField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime
from bson import ObjectId
import os

# MongoDB connection will be initialized in app.py
# This is just a placeholder for compatibility
class DummyDB:
    """Dummy class for compatibility with existing code"""
    pass

db = DummyDB()

# Helper to convert ObjectId to string for JSON serialization
def to_dict(doc):
    """Convert MongoEngine document to dict with string IDs"""
    data = doc.to_mongo().to_dict()
    data['id'] = str(data['_id'])
    del data['_id']
    # Convert datetime objects to ISO format strings
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            data[key] = str(value)
    return data

# Branch Model
class Branch(Document):
    meta = {'collection': 'branches'}

    name = StringField(required=True, max_length=100)  # e.g., "T. Nagar", "Anna Nagar"
    address = StringField(max_length=200)
    city = StringField(max_length=50, default='Chennai')
    phone = StringField(max_length=15)
    email = StringField(max_length=100)
    gstin = StringField(max_length=20)  # GST Identification Number for invoices
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Customer Model
class Customer(Document):
    meta = {'collection': 'customers'}
    
    mobile = StringField(required=True, unique=True, max_length=15)
    first_name = StringField(max_length=100)
    last_name = StringField(max_length=100)
    email = StringField(max_length=100)
    source = StringField(max_length=50)  # Facebook, Instagram, Walk-in, Referral, etc.
    gender = StringField(max_length=10)
    dob = DateField()
    dob_range = StringField(max_length=20)  # Young, Mid, Old
    referral_code = StringField(max_length=50, unique=True, sparse=True)
    whatsapp_consent = BooleanField(default=False)  # Phase 4: WhatsApp consent
    last_visit_date = DateField()  # Phase 4: Computed from bills
    total_visits = IntField(default=0)  # Phase 4: Computed
    total_spent = FloatField(default=0.0)  # Phase 4: Computed
    branch = ReferenceField('Branch')  # Multi-branch: Customer's branch
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Staff Model
class Staff(Document):
    meta = {'collection': 'staffs'}

    mobile = StringField(required=True, unique=True, max_length=15)
    first_name = StringField(required=True, max_length=100)
    last_name = StringField(max_length=100)
    email = StringField(max_length=100)
    salary = FloatField()
    commission_rate = FloatField(default=0.0)  # Percentage
    status = StringField(max_length=20, default='active')  # active, inactive
    role = StringField(max_length=20, default='staff')  # staff, manager, owner
    password_hash = StringField(max_length=255)  # Optional for manager/owner roles
    is_active = BooleanField(default=True)  # For login access control
    branch = ReferenceField('Branch')  # Multi-branch: Staff's assigned branch
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Service Group Model
class ServiceGroup(Document):
    meta = {'collection': 'service_groups'}
    
    name = StringField(required=True, max_length=100)
    display_order = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)

# Service Model
class Service(Document):
    meta = {'collection': 'services'}
    
    name = StringField(required=True, max_length=100)
    group = ReferenceField('ServiceGroup', required=True)
    price = FloatField(required=True)
    duration = IntField()  # Duration in minutes
    description = StringField()
    status = StringField(max_length=20, default='active')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Product Category Model
class ProductCategory(Document):
    meta = {'collection': 'product_categories'}
    
    name = StringField(required=True, max_length=100)
    display_order = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)

# Product Model
class Product(Document):
    meta = {'collection': 'products'}
    
    name = StringField(required=True, max_length=100)
    category = ReferenceField('ProductCategory', required=True)
    price = FloatField(required=True)
    cost = FloatField()  # Cost price
    stock_quantity = IntField(default=0)
    min_stock_level = IntField(default=0)
    sku = StringField(max_length=50)
    description = StringField()
    status = StringField(max_length=20, default='active')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Package Model
class Package(Document):
    meta = {'collection': 'packages'}
    
    name = StringField(required=True, max_length=100)
    price = FloatField(required=True)
    description = StringField()
    services = StringField()  # JSON string of service IDs
    status = StringField(max_length=20, default='active')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Prepaid Group Model
class PrepaidGroup(Document):
    meta = {'collection': 'prepaid_groups'}
    
    name = StringField(required=True, max_length=100)
    display_order = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)

# Prepaid Package Model
class PrepaidPackage(Document):
    meta = {'collection': 'prepaid_packages'}
    
    name = StringField(required=True, max_length=100)
    group = ReferenceField('PrepaidGroup')
    price = FloatField(required=True)
    customer = ReferenceField('Customer')
    branch = ReferenceField('Branch')  # Multi-branch: Prepaid package's branch
    remaining_balance = FloatField(default=0.0)
    purchase_date = DateTimeField()
    expiry_date = DateTimeField()
    status = StringField(max_length=20, default='active')  # active, expired, used
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Membership Plan Model (Template for membership plans)
class MembershipPlan(Document):
    meta = {'collection': 'membership_plans'}
    
    name = StringField(required=True, max_length=100)
    validity_days = IntField(required=True)  # Validity in days
    price = FloatField(required=True)
    allocated_discount = FloatField(default=0.0)  # Discount percentage
    status = StringField(max_length=20, default='active')  # active, inactive
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Membership Model (Customer purchases)
class Membership(Document):
    meta = {'collection': 'memberships'}
    
    name = StringField(required=True, max_length=100)
    customer = ReferenceField('Customer', required=True)
    plan = ReferenceField('MembershipPlan')  # Reference to plan template
    branch = ReferenceField('Branch')  # Multi-branch: Membership's branch
    price = FloatField(required=True)
    purchase_date = DateTimeField(required=True)
    expiry_date = DateTimeField(required=True)
    benefits = StringField()  # JSON string of benefits
    status = StringField(max_length=20, default='active')  # active, expired
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Bill Item Embedded Document (for embedding in Bill)
class BillItemEmbedded(EmbeddedDocument):
    item_type = StringField(required=True, max_length=20)  # service, package, product, prepaid, membership
    service = ReferenceField('Service')
    package = ReferenceField('Package')
    product = ReferenceField('Product')
    prepaid = ReferenceField('PrepaidPackage')
    membership = ReferenceField('Membership')
    staff = ReferenceField('Staff')
    start_time = StringField()  # Store as string in HH:MM:SS format
    price = FloatField(required=True)
    discount = FloatField(default=0.0)
    quantity = IntField(default=1)
    total = FloatField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

# Bill Model
class Bill(Document):
    meta = {
        'collection': 'bills',
        'strict': False  # Allow legacy/unknown fields in existing documents
    }
    
    bill_number = StringField(required=True, unique=True, max_length=50)
    customer = ReferenceField('Customer')
    branch = ReferenceField('Branch')  # Multi-branch: Bill's branch
    appointment = ReferenceField('Appointment')  # Link bill to appointment for consolidation
    bill_date = DateTimeField(required=True, default=datetime.utcnow)
    subtotal = FloatField(default=0.0)
    discount_amount = FloatField(default=0.0)
    discount_type = StringField(max_length=10)  # fix, percentage
    tax_amount = FloatField(default=0.0)
    tax_rate = FloatField(default=0.0)
    final_amount = FloatField(required=True)
    payment_mode = StringField(max_length=20)  # cash, upi, card
    booking_status = StringField(max_length=20, default='service-completed')  # service-completed, confirmed, pending, cancelled
    booking_note = StringField()
    is_deleted = BooleanField(default=False)
    deleted_at = DateTimeField()
    deletion_reason = StringField()
    discount_requested_by = ReferenceField('Staff')  # Phase 5: Who requested discount
    discount_approval_status = StringField(max_length=20, choices=['none', 'pending', 'approved', 'rejected'], default='none')  # Phase 5
    discount_approval_request = ReferenceField('DiscountApprovalRequest')  # Phase 5
    items = ListField(EmbeddedDocumentField(BillItemEmbedded), default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Appointment Model
class Appointment(Document):
    meta = {'collection': 'appointments'}
    
    customer = ReferenceField('Customer', required=True)
    staff = ReferenceField('Staff', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Appointment's branch
    service = ReferenceField('Service')
    appointment_date = DateField(required=True)
    start_time = StringField(required=True)  # Store as string in HH:MM:SS format
    end_time = StringField()  # Store as string in HH:MM:SS format
    status = StringField(max_length=20, default='confirmed')  # confirmed, completed, cancelled, no-show
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Expense Category Model
class ExpenseCategory(Document):
    meta = {'collection': 'expense_categories'}
    
    name = StringField(required=True, max_length=100)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

# Expense Model
class Expense(Document):
    meta = {'collection': 'expenses'}
    
    category = ReferenceField('ExpenseCategory', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Expense's branch
    name = StringField(required=True, max_length=100)
    amount = FloatField(required=True)
    payment_mode = StringField(max_length=20)  # cash, card, upi
    expense_date = DateField(required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Supplier Model
class Supplier(Document):
    meta = {'collection': 'suppliers'}
    
    name = StringField(required=True, max_length=100)
    contact_no = StringField(max_length=15)
    email = StringField(max_length=100)
    address = StringField()
    status = StringField(max_length=20, default='active')
    branch = ReferenceField('Branch')  # Multi-branch: Supplier's assigned branch
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Order Item Embedded Document
class OrderItemEmbedded(EmbeddedDocument):
    product = ReferenceField('Product', required=True)
    quantity = IntField(required=True)
    unit_price = FloatField(required=True)
    total = FloatField(required=True)

# Order Model
class Order(Document):
    meta = {'collection': 'orders'}
    
    supplier = ReferenceField('Supplier', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Order's branch
    order_date = DateField(required=True)
    total_amount = FloatField(required=True)
    status = StringField(max_length=20, default='pending')  # pending, received, cancelled
    notes = StringField()
    order_items = ListField(EmbeddedDocumentField(OrderItemEmbedded), default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Lead Model
class Lead(Document):
    meta = {'collection': 'leads'}
    
    name = StringField(required=True, max_length=100)
    mobile = StringField(max_length=15)
    branch = ReferenceField('Branch')  # Multi-branch: Lead's branch
    email = StringField(max_length=100)
    source = StringField(max_length=50)
    status = StringField(max_length=20, default='new')  # new, contacted, follow-up, completed, lost
    notes = StringField()
    follow_up_date = DateTimeField()
    converted_to_customer = BooleanField(default=False)
    customer = ReferenceField('Customer')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Feedback Model
class Feedback(Document):
    meta = {'collection': 'feedbacks'}
    
    customer = ReferenceField('Customer')
    bill = ReferenceField('Bill')
    staff = ReferenceField('Staff')  # Link feedback to staff member
    branch = ReferenceField('Branch')  # Multi-branch: Feedback's branch
    rating = IntField()  # 1-5
    comment = StringField()
    google_review_eligible = BooleanField(default=False)  # Phase 3: Rating >= 4
    google_review_link_clicked = BooleanField(default=False)  # Phase 3
    google_review_link_clicked_at = DateTimeField()  # Phase 3
    service_recovery_required = BooleanField(default=False)  # Phase 3: Rating <= 3
    created_at = DateTimeField(default=datetime.utcnow)

# Staff Attendance Model
class StaffAttendance(Document):
    meta = {'collection': 'staff_attendance'}
    
    staff = ReferenceField('Staff', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Attendance's branch
    attendance_date = DateField(required=True)
    check_in_time = StringField()  # Store as string in HH:MM:SS format
    check_out_time = StringField()  # Store as string in HH:MM:SS format
    status = StringField(max_length=20, default='present')  # present, absent, late, half-day
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Asset Model
class Asset(Document):
    meta = {'collection': 'assets'}
    
    name = StringField(required=True, max_length=100)
    category = StringField(max_length=50)
    branch = ReferenceField('Branch')  # Multi-branch: Asset's branch
    purchase_date = DateField()
    purchase_price = FloatField()
    current_value = FloatField()
    depreciation_rate = FloatField()
    status = StringField(max_length=20, default='active')  # active, disposed, maintenance
    location = StringField(max_length=100)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Cash Transaction Model
class CashTransaction(Document):
    meta = {'collection': 'cash_transactions'}
    
    transaction_type = StringField(required=True, max_length=20)  # in, out
    branch = ReferenceField('Branch')  # Multi-branch: Transaction's branch
    amount = FloatField(required=True)
    reason = StringField(max_length=200)
    notes = StringField()
    transaction_date = DateField(required=True)
    transaction_time = StringField(required=True)  # Store as string in HH:MM:SS format
    created_at = DateTimeField(default=datetime.utcnow)

# Referral Program Settings Model
class ReferralProgramSettings(Document):
    meta = {'collection': 'referral_program_settings'}
    
    enabled = BooleanField(default=False)
    reward_type = StringField(max_length=20, default='percentage')  # percentage, fixed
    referrer_reward_percentage = FloatField(default=5.0)  # Bonus credited to existing customer
    referee_reward_percentage = FloatField(default=5.0)  # Discount applied to new customer's first bill
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings = cls.objects.first()
        if not settings:
            settings = cls(
                enabled=False,
                reward_type='percentage',
                referrer_reward_percentage=5.0,
                referee_reward_percentage=5.0
            )
            settings.save()
        return settings

# Tax Settings Model
class TaxSettings(Document):
    meta = {'collection': 'tax_settings'}
    
    gst_number = StringField(max_length=50)
    service_pricing_type = StringField(max_length=20, default='inclusive')  # inclusive, exclusive
    product_pricing_type = StringField(max_length=20, default='exclusive')  # inclusive, exclusive
    prepaid_pricing_type = StringField(max_length=20, default='inclusive')  # inclusive, exclusive
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings = cls.objects.first()
        if not settings:
            settings = cls(
                gst_number='',
                service_pricing_type='inclusive',
                product_pricing_type='exclusive',
                prepaid_pricing_type='inclusive'
            )
            settings.save()
        return settings

# Tax Slab Model
class TaxSlab(Document):
    meta = {'collection': 'tax_slabs'}
    
    name = StringField(required=True, max_length=100)
    rate = FloatField(required=True)  # Tax rate percentage
    apply_to_services = BooleanField(default=False)
    apply_to_products = BooleanField(default=False)
    apply_to_prepaid = BooleanField(default=False)
    status = StringField(max_length=20, default='active')  # active, inactive
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Manager Model
class Manager(Document):
    meta = {'collection': 'managers'}

    first_name = StringField(required=True, max_length=100)
    last_name = StringField(max_length=100)
    email = StringField(required=True, unique=True, max_length=100)
    mobile = StringField(required=True, unique=True, max_length=15)
    salon = StringField(max_length=200)  # Saloon name or account
    password_hash = StringField(max_length=255)  # Hashed password using bcrypt
    role = StringField(max_length=20, default='manager')  # manager only (owners are in separate collection)
    permissions = ListField(StringField())  # Optional custom permissions
    is_active = BooleanField(default=True)  # For login access control
    status = StringField(max_length=20, default='active')  # active, inactive
    branch = ReferenceField('Branch')  # Multi-branch: Manager's assigned branch
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Owner Model - Separate collection for owners
class Owner(Document):
    meta = {'collection': 'owners'}

    first_name = StringField(required=True, max_length=100)
    last_name = StringField(max_length=100)
    email = StringField(required=True, unique=True, max_length=100)
    mobile = StringField(required=True, unique=True, max_length=15)
    salon = StringField(max_length=200)  # Saloon name or account
    password_hash = StringField(max_length=255)  # Hashed password using bcrypt
    permissions = ListField(StringField())  # Optional custom permissions
    is_active = BooleanField(default=True)  # For login access control
    status = StringField(max_length=20, default='active')  # active, inactive
    # Owner doesn't belong to a specific branch - has access to all branches
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Login History Model - Track all login/signup events
class LoginHistory(Document):
    meta = {'collection': 'login_history'}
    
    user_id = StringField(required=True)  # Staff or Manager ID
    user_type = StringField(required=True, max_length=20)  # staff, manager
    role = StringField(required=True, max_length=20)  # staff, manager, owner
    login_method = StringField(max_length=20, default='password')  # password, role_selection
    ip_address = StringField(max_length=50)
    user_agent = StringField(max_length=500)
    login_status = StringField(max_length=20, default='success')  # success, failed
    failure_reason = StringField()  # If login failed
    created_at = DateTimeField(default=datetime.utcnow)

# Missed Enquiry Model (Phase 2)
class MissedEnquiry(Document):
    meta = {'collection': 'missed_enquiries'}
    
    customer_name = StringField(required=True, max_length=100)
    customer_phone = StringField(required=True, max_length=15)
    branch = ReferenceField('Branch')  # Multi-branch: Missed enquiry's branch
    enquiry_type = StringField(max_length=20, choices=['walk-in', 'call', 'whatsapp', 'other'], default='walk-in')
    requested_service = StringField(max_length=200)
    requested_product = StringField(max_length=200)
    reason_not_delivered = StringField(max_length=500)
    follow_up_date = DateField()
    status = StringField(max_length=20, choices=['open', 'converted', 'lost'], default='open')
    converted_to_appointment = ReferenceField('Appointment')
    notes = StringField()
    created_by = ReferenceField('Staff')  # Can be staff or manager
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Service Recovery Case Model (Phase 3)
class ServiceRecoveryCase(Document):
    meta = {'collection': 'service_recovery_cases'}
    
    feedback = ReferenceField('Feedback', required=True)
    customer = ReferenceField('Customer', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Service recovery case's branch
    bill = ReferenceField('Bill')
    issue_type = StringField(max_length=50, choices=['service_quality', 'staff_behavior', 'pricing', 'other'], default='other')
    description = StringField(max_length=1000)
    assigned_manager = ReferenceField('Manager')
    resolution_notes = StringField(max_length=1000)
    status = StringField(max_length=20, choices=['open', 'in_progress', 'resolved', 'closed'], default='open')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    resolved_at = DateTimeField()

# WhatsApp Template Model (Phase 4)
class WhatsAppTemplate(Document):
    meta = {'collection': 'whatsapp_templates'}
    
    name = StringField(required=True, max_length=100)
    message_text = StringField(required=True, max_length=1000)
    category = StringField(max_length=50, choices=['promotional', 'transactional', 'service_reminder'], default='promotional')
    status = StringField(max_length=20, choices=['active', 'inactive'], default='inactive')
    approved_by = ReferenceField('Manager')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# WhatsApp Message Model (Phase 4)
class WhatsAppMessage(Document):
    meta = {'collection': 'whatsapp_messages'}
    
    customer = ReferenceField('Customer', required=True)
    template = ReferenceField('WhatsAppTemplate')
    branch = ReferenceField('Branch')  # Multi-branch: WhatsApp message's branch
    message_text = StringField(required=True, max_length=1000)
    segment = StringField(max_length=50, choices=['new', 'regular', 'loyal', 'inactive', 'high_spending', 'custom'])
    delivery_status = StringField(max_length=20, choices=['sent', 'delivered', 'failed', 'pending'], default='pending')
    sent_by = ReferenceField('Staff')  # Can be staff or manager
    sent_at = DateTimeField(default=datetime.utcnow)
    delivery_timestamp = DateTimeField()

# Discount Approval Request Model (Phase 5)
class DiscountApprovalRequest(Document):
    meta = {'collection': 'discount_approval_requests'}
    
    bill = ReferenceField('Bill', required=True)
    requested_by = ReferenceField('Staff', required=True)
    branch = ReferenceField('Branch')  # Multi-branch: Discount approval's branch
    requested_discount_percent = FloatField(required=True)
    requested_discount_amount = FloatField(required=True)
    reason = StringField(required=True, max_length=500)
    approval_status = StringField(max_length=20, choices=['pending', 'approved', 'rejected'], default='pending')
    approved_by = ReferenceField('Manager')
    approval_code_used = StringField(max_length=255)  # Hashed approval code
    approval_method = StringField(max_length=20, choices=['in_app', 'code'], default='in_app')
    approved_at = DateTimeField()
    notes = StringField(max_length=500)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Approval Code Model (Phase 5)
class ApprovalCode(Document):
    meta = {'collection': 'approval_codes'}
    
    code_hash = StringField(required=True, max_length=255)  # Hashed approval code
    role = StringField(required=True, max_length=20, choices=['manager', 'owner'])
    created_by = ReferenceField('Manager', required=True)
    is_active = BooleanField(default=True)
    usage_count = IntField(default=0)
    max_uses = IntField()  # Optional limit
    expires_at = DateTimeField()  # Optional expiration
    created_at = DateTimeField(default=datetime.utcnow)

# Staff Leave Model
class StaffLeave(Document):
    """Tracks staff leave/absence requests"""
    meta = {'collection': 'staff_leaves'}
    
    staff = ReferenceField('Staff', required=True)
    branch = ReferenceField('Branch', required=True)
    start_date = DateField(required=True)
    end_date = DateField(required=True)
    leave_type = StringField(max_length=30, default='casual', choices=['casual', 'sick', 'vacation', 'emergency', 'other'])
    reason = StringField(max_length=500)
    status = StringField(max_length=20, default='pending', choices=['pending', 'approved', 'rejected', 'cancelled'])
    coverage_required = BooleanField(default=True)
    covered_by = ReferenceField('StaffTempAssignment')  # Links to temp assignment
    approved_by = ReferenceField('Staff')
    rejection_reason = StringField(max_length=500)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Staff Temporary Assignment Model
class StaffTempAssignment(Document):
    """Tracks temporary staff assignments to different branches"""
    meta = {'collection': 'staff_temp_assignments'}
    
    staff = ReferenceField('Staff', required=True)
    original_branch = ReferenceField('Branch', required=True)  # Home branch
    temp_branch = ReferenceField('Branch', required=True)  # Covering branch
    start_date = DateField(required=True)
    end_date = DateField(required=True)
    reason = StringField(max_length=50, default='leave_coverage', choices=['leave_coverage', 'training', 'support', 'event', 'other'])
    covering_for = ReferenceField('Staff')  # Optional: Staff member on leave
    related_leave = ReferenceField('StaffLeave')  # Optional: Link to leave request
    notes = StringField(max_length=500)
    status = StringField(max_length=20, default='active', choices=['active', 'completed', 'cancelled'])
    created_by = ReferenceField('Staff')  # Who created this assignment
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Backward compatibility aliases for routes not yet converted
# These allow old route imports to work but routes need conversion to use embedded documents
BillItem = BillItemEmbedded  # Temporary alias - routes should use Bill.items instead
OrderItem = OrderItemEmbedded  # Temporary alias - routes should use Order.order_items instead
