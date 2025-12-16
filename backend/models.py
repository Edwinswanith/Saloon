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
    loyalty_points = IntField(default=0)
    referral_code = StringField(max_length=50, unique=True, sparse=True)
    wallet_balance = FloatField(default=0.0)
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
    meta = {'collection': 'bills'}
    
    bill_number = StringField(required=True, unique=True, max_length=50)
    customer = ReferenceField('Customer')
    bill_date = DateTimeField(required=True, default=datetime.utcnow)
    subtotal = FloatField(default=0.0)
    discount_amount = FloatField(default=0.0)
    discount_type = StringField(max_length=10)  # fix, percentage
    tax_amount = FloatField(default=0.0)
    tax_rate = FloatField(default=0.0)
    final_amount = FloatField(required=True)
    payment_mode = StringField(max_length=20)  # cash, upi, card, wallet
    booking_status = StringField(max_length=20, default='service-completed')  # service-completed, confirmed, pending, cancelled
    booking_note = StringField()
    is_deleted = BooleanField(default=False)
    deleted_at = DateTimeField()
    deletion_reason = StringField()
    items = ListField(EmbeddedDocumentField(BillItemEmbedded), default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Appointment Model
class Appointment(Document):
    meta = {'collection': 'appointments'}
    
    customer = ReferenceField('Customer', required=True)
    staff = ReferenceField('Staff', required=True)
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
    rating = IntField()  # 1-5
    comment = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

# Staff Attendance Model
class StaffAttendance(Document):
    meta = {'collection': 'staff_attendance'}
    
    staff = ReferenceField('Staff', required=True)
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
    amount = FloatField(required=True)
    reason = StringField(max_length=200)
    notes = StringField()
    transaction_date = DateField(required=True)
    transaction_time = StringField(required=True)  # Store as string in HH:MM:SS format
    created_at = DateTimeField(default=datetime.utcnow)

# Loyalty Program Settings Model
class LoyaltyProgramSettings(Document):
    meta = {'collection': 'loyalty_program_settings'}
    
    enabled = BooleanField(default=False)
    earning_rate = FloatField(default=100.0)  # Amount customer must spend to earn 1 point
    redemption_rate = FloatField(default=1.0)  # Number of points needed to redeem for ₹1
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings = cls.objects.first()
        if not settings:
            settings = cls(enabled=False, earning_rate=100.0, redemption_rate=1.0)
            settings.save()
        return settings

# Referral Program Settings Model
class ReferralProgramSettings(Document):
    meta = {'collection': 'referral_program_settings'}
    
    enabled = BooleanField(default=False)
    reward_type = StringField(max_length=20, default='percentage')  # percentage, fixed
    referrer_reward_percentage = FloatField(default=5.0)  # Bonus credited to existing customer's wallet
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
    salon = StringField(max_length=200)  # Salon name or account
    password = StringField(max_length=255)  # For login (can be hashed later)
    status = StringField(max_length=20, default='active')  # active, inactive
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

# Backward compatibility aliases for routes not yet converted
# These allow old route imports to work but routes need conversion to use embedded documents
BillItem = BillItemEmbedded  # Temporary alias - routes should use Bill.items instead
OrderItem = OrderItemEmbedded  # Temporary alias - routes should use Order.order_items instead
