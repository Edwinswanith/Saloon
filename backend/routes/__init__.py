from flask import Blueprint
from .auth_routes import auth_bp
from .customer_routes import customer_bp
from .staff_routes import staff_bp
from .service_routes import service_bp
from .product_routes import product_bp
from .package_routes import package_bp
from .prepaid_routes import prepaid_bp
from .bill_routes import bill_bp
from .appointment_routes import appointment_bp
from .expense_routes import expense_bp
from .inventory_routes import inventory_bp
from .dashboard_routes import dashboard_bp
from .report_routes import report_bp
from .client_value_routes import client_value_bp
from .lead_routes import lead_bp
from .feedback_routes import feedback_bp
from .attendance_routes import attendance_bp
from .asset_routes import asset_bp
from .cash_routes import cash_bp
from .membership_plan_routes import membership_plan_bp
from .loyalty_program_routes import loyalty_program_bp
from .referral_program_routes import referral_program_bp
from .tax_routes import tax_bp
from .manager_routes import manager_bp
from .missed_enquiry_routes import missed_enquiry_bp
from .service_recovery_routes import service_recovery_bp
from .customer_lifecycle_routes import customer_lifecycle_bp
from .discount_approval_routes import discount_approval_bp
from .branch_routes import branch_bp

def register_routes(app):
    # Register blueprints with /api prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customer_bp, url_prefix='/api/customers')
    app.register_blueprint(staff_bp, url_prefix='/api/staffs')
    app.register_blueprint(service_bp, url_prefix='/api/services')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(package_bp, url_prefix='/api/packages')
    app.register_blueprint(prepaid_bp, url_prefix='/api/prepaid')
    app.register_blueprint(bill_bp, url_prefix='/api')
    app.register_blueprint(appointment_bp, url_prefix='/api')
    app.register_blueprint(expense_bp, url_prefix='/api/expenses')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(client_value_bp)
    app.register_blueprint(lead_bp, url_prefix='/api/leads')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(asset_bp, url_prefix='/api/assets')
    app.register_blueprint(cash_bp, url_prefix='/api/cash')
    app.register_blueprint(membership_plan_bp, url_prefix='/api/membership-plans')
    app.register_blueprint(loyalty_program_bp, url_prefix='/api/loyalty-program')
    app.register_blueprint(referral_program_bp, url_prefix='/api/referral-program')
    app.register_blueprint(tax_bp, url_prefix='/api/tax')
    app.register_blueprint(manager_bp, url_prefix='/api/managers')
    app.register_blueprint(missed_enquiry_bp, url_prefix='/api/missed-enquiries')
    app.register_blueprint(service_recovery_bp, url_prefix='/api/service-recovery')
    app.register_blueprint(customer_lifecycle_bp, url_prefix='/api/customer-lifecycle')
    app.register_blueprint(discount_approval_bp, url_prefix='/api/discount-approvals')
    app.register_blueprint(branch_bp, url_prefix='/api')

