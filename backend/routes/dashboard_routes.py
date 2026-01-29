from flask import Blueprint, request, jsonify
from models import Bill, Customer, Staff, Expense, Product, Appointment, Lead, Feedback, Service, Package
from datetime import datetime, timedelta, date
from mongoengine import Q
from mongoengine.errors import DoesNotExist
from bson import ObjectId
import traceback
from utils.auth import require_auth
from utils.branch_filter import get_selected_branch, filter_by_branch
from utils.date_utils import get_ist_date_range, ist_to_utc_start, ist_to_utc_end, get_ist_today
from utils.redis_cache import cache_response
from utils.performance import log_performance

dashboard_bp = Blueprint('dashboard', __name__)

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def get_safe_customer_info(customer_ref):
    """Safely extract customer info, handling deleted references"""
    if not customer_ref:
        return {'name': 'Walk-in', 'mobile': None, 'id': None, 'source': None, 'email': None}
    
    try:
        # Try to reload if it's a DBRef
        if hasattr(customer_ref, 'reload'):
            try:
                customer_ref.reload()
            except:
                # Customer deleted, return default
                return {'name': 'Walk-in', 'mobile': None, 'id': None, 'source': None, 'email': None}
        
        # Check if customer has required attributes
        if hasattr(customer_ref, 'first_name'):
            return {
                'name': f"{customer_ref.first_name or ''} {customer_ref.last_name or ''}".strip() or 'Walk-in',
                'mobile': getattr(customer_ref, 'mobile', None),
                'id': str(customer_ref.id) if hasattr(customer_ref, 'id') else None,
                'source': getattr(customer_ref, 'source', None),
                'email': getattr(customer_ref, 'email', None)
            }
    except Exception:
        pass
    
    return {'name': 'Walk-in', 'mobile': None, 'id': None, 'source': None, 'email': None}

@dashboard_bp.route('/stats', methods=['GET'])
@require_auth
@cache_response(ttl=300)  # Cache for 5 minutes
@log_performance
def get_dashboard_stats(current_user=None):
    """Get overall dashboard statistics - OPTIMIZED with MongoDB aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Default to last 30 days if no date range provided (using IST)
        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)

        # OPTIMIZED: Use MongoDB aggregation for bills stats instead of loading all into memory
        try:
            match_stage = {
                "is_deleted": False,
                "bill_date": {"$gte": start, "$lte": end}
            }
            if branch:
                # Convert branch.id to ObjectId for MongoDB aggregation
                match_stage["branch"] = ObjectId(str(branch.id))

            bills_pipeline = [
                {"$match": match_stage},
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$final_amount"},
                    "total_transactions": {"$sum": 1},
                    "total_tax": {"$sum": {"$ifNull": ["$tax_amount", 0]}},
                    "deleted_count": {"$sum": {"$cond": ["$is_deleted", 1, 0]}},
                    "deleted_amount": {"$sum": {"$cond": ["$is_deleted", "$final_amount", 0]}}
                }}
            ]

            bills_result = list(Bill.objects.aggregate(bills_pipeline))
            if bills_result:
                total_revenue = bills_result[0].get('total_revenue', 0) or 0
                total_transactions = bills_result[0].get('total_transactions', 0)
                total_tax = bills_result[0].get('total_tax', 0) or 0
                deleted_bills_count = bills_result[0].get('deleted_count', 0) or 0
                deleted_bills_amount = bills_result[0].get('deleted_amount', 0) or 0
            else:
                total_revenue = 0
                total_transactions = 0
                total_tax = 0
                deleted_bills_count = 0
                deleted_bills_amount = 0
        except Exception as e:
            print(f"[DASHBOARD STATS] Error in bills aggregation: {str(e)}")
            print(f"[DASHBOARD STATS] Traceback: {traceback.format_exc()}")
            # Set defaults on error
            total_revenue = 0
            total_transactions = 0
            total_tax = 0
            deleted_bills_count = 0
            deleted_bills_amount = 0

        avg_bill_value = float(total_revenue) / int(total_transactions) if total_transactions > 0 else 0.0

        # Convert dates for use in queries (date objects for MongoEngine queries, datetime for aggregation)
        ist_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        ist_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # OPTIMIZED: Use aggregation for expenses
        try:
            # Convert to datetime (not date) for MongoDB aggregation
            ist_start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            ist_end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end datetime to end of day
            ist_end_datetime = ist_end_datetime.replace(hour=23, minute=59, second=59)

            expenses_match = {
                "expense_date": {"$gte": ist_start_datetime, "$lte": ist_end_datetime}
            }
            if branch:
                # Convert branch.id to ObjectId for MongoDB aggregation
                expenses_match["branch"] = ObjectId(str(branch.id))

            expenses_pipeline = [
                {"$match": expenses_match},
                {"$group": {
                    "_id": None,
                    "total_expenses": {"$sum": "$amount"}
                }}
            ]

            expenses_result = list(Expense.objects.aggregate(expenses_pipeline))
            total_expenses = expenses_result[0].get('total_expenses', 0) if expenses_result else 0
        except Exception as e:
            print(f"[DASHBOARD STATS] Error in expenses aggregation: {str(e)}")
            print(f"[DASHBOARD STATS] Traceback: {traceback.format_exc()}")
            total_expenses = 0

        # Net profit
        net_profit = float(total_revenue) - float(total_expenses)

        # Use .count() for other stats (efficient with indexes)
        customers_query = Customer.objects
        if branch:
            customers_query = customers_query.filter(branch=branch)
        total_customers = customers_query.count()

        new_customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            new_customers_query = new_customers_query.filter(branch=branch)
        new_customers = new_customers_query.count()

        staff_query = Staff.objects(status='active')
        if branch:
            staff_query = staff_query.filter(branch=branch)
        active_staff = staff_query.count()

        # Appointments stats with branch filter
        appt_query = Appointment.objects(
            appointment_date__gte=ist_start_date,
            appointment_date__lte=ist_end_date
        )
        if branch:
            appt_query = appt_query.filter(branch=branch)
        total_appointments = appt_query.count()

        completed_appt_query = Appointment.objects(
            appointment_date__gte=ist_start_date,
            appointment_date__lte=ist_end_date,
            status='completed'
        )
        if branch:
            completed_appt_query = completed_appt_query.filter(branch=branch)
        completed_appointments = completed_appt_query.count()

        return jsonify({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'average_per_transaction': round(avg_bill_value, 2)
            },
            'transactions': {
                'total': total_transactions
            },
            'tax': {
                'total': round(total_tax, 2)
            },
            'deleted_bills': {
                'count': deleted_bills_count,
                'amount': round(deleted_bills_amount, 2)
            },
            'expenses': {
                'total': round(total_expenses, 2)
            },
            'profit': {
                'net': round(net_profit, 2),
                'margin': round((float(net_profit) / float(total_revenue) * 100) if total_revenue > 0 else 0, 2)
            },
            'customers': {
                'total': total_customers,
                'new': new_customers
            },
            'staff': {
                'active': active_staff
            },
            'appointments': {
                'total': total_appointments,
                'completed': completed_appointments,
                'completion_rate': round((completed_appointments / total_appointments * 100) if total_appointments > 0 else 0, 2)
            }
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_dashboard_stats: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/staff-performance', methods=['GET'])
@require_auth
@cache_response(ttl=300)  # Cache for 5 minutes
@log_performance
def get_staff_performance(current_user=None):
    """Get staff performance metrics - OPTIMIZED with single aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        branch = get_selected_branch(request, current_user)

        # OPTIMIZED: Single aggregation for all staff performance
        match_stage = {
            "is_deleted": False,
            "bill_date": {"$gte": start, "$lte": end}
        }
        if branch:
            # Convert branch.id to ObjectId for MongoDB aggregation
            match_stage["branch"] = ObjectId(str(branch.id))

        pipeline = [
            {"$match": match_stage},
            {"$unwind": "$items"},
            {"$match": {"items.staff": {"$ne": None}}},
            {"$group": {
                "_id": "$items.staff",
                "total_revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "total_services": {"$sum": {"$ifNull": ["$items.quantity", 1]}},
                "service_count": {
                    "$sum": {"$cond": [
                        {"$eq": [{"$ifNull": ["$items.item_type", "service"]}, "service"]},
                        {"$ifNull": ["$items.quantity", 1]}, 0
                    ]}
                },
                "package_count": {
                    "$sum": {"$cond": [
                        {"$eq": ["$items.item_type", "package"]},
                        {"$ifNull": ["$items.quantity", 1]}, 0
                    ]}
                },
                "product_count": {
                    "$sum": {"$cond": [
                        {"$eq": ["$items.item_type", "product"]},
                        {"$ifNull": ["$items.quantity", 1]}, 0
                    ]}
                },
                "prepaid_count": {
                    "$sum": {"$cond": [
                        {"$eq": ["$items.item_type", "prepaid"]},
                        {"$ifNull": ["$items.quantity", 1]}, 0
                    ]}
                },
                "membership_count": {
                    "$sum": {"$cond": [
                        {"$eq": ["$items.item_type", "membership"]},
                        {"$ifNull": ["$items.quantity", 1]}, 0
                    ]}
                }
            }},
            {"$lookup": {
                "from": "staffs",
                "localField": "_id",
                "foreignField": "_id",
                "as": "staff_doc"
            }},
            {"$unwind": {"path": "$staff_doc", "preserveNullAndEmptyArrays": True}},
            {"$match": {"staff_doc.status": "active"}},
            {"$project": {
                "staff_id": {"$toString": "$_id"},
                "staff_name": {
                    "$concat": [
                        {"$ifNull": ["$staff_doc.first_name", ""]},
                        " ",
                        {"$ifNull": ["$staff_doc.last_name", ""]}
                    ]
                },
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "total_services": 1,
                "service_count": 1,
                "package_count": 1,
                "product_count": 1,
                "prepaid_count": 1,
                "membership_count": 1,
                "commission_rate": {"$ifNull": ["$staff_doc.commission_rate", 0]}
            }},
            {"$addFields": {
                "commission_earned": {
                    "$round": [{"$multiply": ["$total_revenue", {"$divide": ["$commission_rate", 100]}]}, 2]
                }
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 50}
        ]

        performance_results = list(Bill.objects.aggregate(pipeline))

        # Get staff IDs from aggregation results for appointment counts
        staff_ids = [r.get('_id') for r in performance_results if r.get('_id')]

        # Batch fetch appointment counts for all staff
        appt_counts = {}
        if staff_ids:
            # Convert to datetime for MongoDB aggregation (even though appointment_date is a DateField)
            # MongoDB aggregation cannot encode Python date objects
            appt_start_datetime = start.replace(hour=0, minute=0, second=0, microsecond=0)
            appt_end_datetime = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            appt_pipeline = [
                {"$match": {
                    "staff": {"$in": staff_ids},
                    "appointment_date": {"$gte": appt_start_datetime, "$lte": appt_end_datetime},
                    "status": "completed"
                }},
                {"$group": {
                    "_id": "$staff",
                    "count": {"$sum": 1}
                }}
            ]
            appt_results = list(Appointment.objects.aggregate(appt_pipeline))
            appt_counts = {str(r['_id']): r['count'] for r in appt_results}

        # Format final response
        performance = []
        for r in performance_results:
            staff_id = r.get('staff_id', '')
            performance.append({
                'staff_id': staff_id,
                'staff_name': r.get('staff_name', '').strip(),
                'total_revenue': r.get('total_revenue', 0),
                'total_services': r.get('total_services', 0),
                'service_count': r.get('service_count', 0),
                'package_count': r.get('package_count', 0),
                'product_count': r.get('product_count', 0),
                'prepaid_count': r.get('prepaid_count', 0),
                'membership_count': r.get('membership_count', 0),
                'commission_earned': r.get('commission_earned', 0),
                'completed_appointments': appt_counts.get(staff_id, 0)
            })

        return jsonify(performance)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/top-customers', methods=['GET'])
@require_auth
@cache_response(ttl=60)  # Cache for 60 seconds
@log_performance
def get_top_customers(current_user=None):
    """Get top customers by revenue - OPTIMIZED with aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        branch = get_selected_branch(request, current_user)

        # Build match stage
        match_stage = {"is_deleted": False, "customer": {"$ne": None}}
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                match_stage["bill_date"] = {"$gte": start}
            if end:
                match_stage.setdefault("bill_date", {})["$lte"] = end
        if branch:
            # Convert branch.id to ObjectId for MongoDB aggregation
            match_stage["branch"] = ObjectId(str(branch.id))

        # OPTIMIZED: Single aggregation pipeline
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$customer",
                "total_spent": {"$sum": {"$ifNull": ["$final_amount", 0]}},
                "visit_count": {"$sum": 1}
            }},
            {"$lookup": {
                "from": "customers",
                "localField": "_id",
                "foreignField": "_id",
                "as": "customer_doc"
            }},
            {"$unwind": "$customer_doc"},
            {"$project": {
                "customer_id": {"$toString": "$_id"},
                "customer_name": {
                    "$trim": {
                        "input": {
                            "$concat": [
                                {"$ifNull": ["$customer_doc.first_name", ""]},
                                " ",
                                {"$ifNull": ["$customer_doc.last_name", ""]}
                            ]
                        }
                    }
                },
                "mobile": "$customer_doc.mobile",
                "total_spent": {"$round": ["$total_spent", 2]},
                "visit_count": 1,
                "average_per_visit": {
                    "$round": [{"$divide": ["$total_spent", "$visit_count"]}, 2]
                }
            }},
            {"$sort": {"total_spent": -1}},
            {"$limit": limit}
        ]

        results = list(Bill.objects.aggregate(pipeline))

        # Format response
        formatted_results = []
        for r in results:
            formatted_results.append({
                'customer_id': r.get('customer_id', ''),
                'customer_name': r.get('customer_name', 'Walk-in').strip() or 'Walk-in',
                'mobile': r.get('mobile'),
                'total_spent': r.get('total_spent', 0),
                'visit_count': r.get('visit_count', 0),
                'average_per_visit': r.get('average_per_visit', 0)
            })

        return jsonify(formatted_results)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/top-offerings', methods=['GET'])
@require_auth
@cache_response(ttl=60)  # Cache for 60 seconds
@log_performance
def get_top_offerings(current_user=None):
    """Get top services/products/packages by revenue - OPTIMIZED with aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Build match stage
        match_stage = {"is_deleted": False}
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                match_stage["bill_date"] = {"$gte": start}
            if end:
                match_stage.setdefault("bill_date", {})["$lte"] = end
        if branch:
            # Convert branch.id to ObjectId for MongoDB aggregation
            match_stage["branch"] = ObjectId(str(branch.id))
        
        # OPTIMIZED: Use aggregation pipeline instead of loading all bills
        pipeline = [
            {"$match": match_stage},
            {"$unwind": "$items"},
            {"$match": {
                "items.item_type": {"$in": ["service", "product", "package"]}
            }},
            {"$group": {
                "_id": {
                    "item_type": "$items.item_type",
                    "item_id": {
                        "$cond": [
                            {"$eq": ["$items.item_type", "service"]},
                            "$items.service",
                            {
                                "$cond": [
                                    {"$eq": ["$items.item_type", "product"]},
                                    "$items.product",
                                    "$items.package"
                                ]
                            }
                        ]
                    }
                },
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "quantity": {"$sum": {"$ifNull": ["$items.quantity", 1]}}
            }},
            {"$lookup": {
                "from": "services",
                "localField": "_id.item_id",
                "foreignField": "_id",
                "as": "service_doc"
            }},
            {"$lookup": {
                "from": "products",
                "localField": "_id.item_id",
                "foreignField": "_id",
                "as": "product_doc"
            }},
            {"$lookup": {
                "from": "packages",
                "localField": "_id.item_id",
                "foreignField": "_id",
                "as": "package_doc"
            }},
            {"$project": {
                "item_type": "$_id.item_type",
                "name": {
                    "$cond": [
                        {"$eq": ["$_id.item_type", "service"]},
                        {"$arrayElemAt": ["$service_doc.name", 0]},
                        {
                            "$cond": [
                                {"$eq": ["$_id.item_type", "product"]},
                                {"$arrayElemAt": ["$product_doc.name", 0]},
                                {"$arrayElemAt": ["$package_doc.name", 0]}
                            ]
                        }
                    ]
                },
                "revenue": {"$round": ["$revenue", 2]},
                "quantity": 1
            }},
            {"$match": {"name": {"$ne": None}}},
            {"$sort": {"revenue": -1}},
            {"$limit": limit}
        ]
        
        results = list(Bill.objects.aggregate(pipeline))
        
        # Format results
        result = []
        for r in results:
            result.append({
                'name': r.get('name', 'Unknown'),
                'type': r.get('item_type', 'unknown'),
                'revenue': r.get('revenue', 0),
                'quantity': r.get('quantity', 0),
                'key': f"{r.get('item_type', 'unknown')}_{r.get('_id', {}).get('item_id', '')}"
            })
        
        return jsonify(result)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/offering-clients', methods=['GET'])
@require_auth
def get_offering_clients(current_user=None):
    """Get customers who purchased a specific offering"""
    try:
        offering_name = request.args.get('name')
        offering_type = request.args.get('type')  # service, product, or package
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not offering_name or not offering_type:
            return jsonify({'error': 'Offering name and type are required'}), 400

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Get bills in date range
        bills_query = Bill.objects(is_deleted=False)
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
            if start:
                bills_query = bills_query.filter(bill_date__gte=start)
            if end:
                bills_query = bills_query.filter(bill_date__lte=end)
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        bills = list(bills_query)
        
        from models import Service, Product, Package
        
        # Find the offering ID
        offering_id = None
        if offering_type == 'service':
            service = Service.objects(name=offering_name).first()
            if service:
                offering_id = str(service.id)
        elif offering_type == 'product':
            product = Product.objects(name=offering_name).first()
            if product:
                offering_id = str(product.id)
        elif offering_type == 'package':
            package = Package.objects(name=offering_name).first()
            if package:
                offering_id = str(package.id)
        
        if not offering_id:
            return jsonify({'error': 'Offering not found'}), 404
        
        # Collect customers who purchased this offering
        customer_purchases = {}
        
        for bill in bills:
            customer_info = get_safe_customer_info(bill.customer)
            if not customer_info['id']:
                continue
                
            customer_id = customer_info['id']
            customer_name = customer_info['name']
            
            for item in (bill.items or []):
                try:
                    item_type = getattr(item, 'item_type', None)
                    if item_type != offering_type:
                        continue
                    
                    item_offering_id = None
                    if item_type == 'service' and hasattr(item, 'service') and item.service:
                        item_offering_id = str(item.service.id) if hasattr(item.service, 'id') else None
                    elif item_type == 'product' and hasattr(item, 'product') and item.product:
                        item_offering_id = str(item.product.id) if hasattr(item.product, 'id') else None
                    elif item_type == 'package' and hasattr(item, 'package') and item.package:
                        item_offering_id = str(item.package.id) if hasattr(item.package, 'id') else None
                    
                    if item_offering_id == offering_id:
                        if customer_id not in customer_purchases:
                            customer_purchases[customer_id] = {
                                'customer_id': customer_id,
                                'customer_name': customer_name or 'Unknown',
                                'mobile': customer_info['mobile'] or '-',
                                'email': customer_info['email'] or '-',
                                'purchase_count': 0,
                                'total_spent': 0.0,
                                'last_purchase_date': None
                            }
                        
                        customer_purchases[customer_id]['purchase_count'] += _safe_int(item.quantity, default=1)
                        customer_purchases[customer_id]['total_spent'] += _safe_float(item.total)
                        
                        # Update last purchase date
                        bill_date = bill.bill_date
                        if bill_date:
                            if not customer_purchases[customer_id]['last_purchase_date'] or bill_date > customer_purchases[customer_id]['last_purchase_date']:
                                customer_purchases[customer_id]['last_purchase_date'] = bill_date
                except (AttributeError, TypeError, ValueError) as e:
                    continue
        
        # Convert to list and sort by total spent
        clients = sorted(
            customer_purchases.values(),
            key=lambda x: x['total_spent'],
            reverse=True
        )
        
        # Format dates
        for client in clients:
            if client['last_purchase_date']:
                if isinstance(client['last_purchase_date'], datetime):
                    client['last_purchase_date'] = client['last_purchase_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'offering': {
                'name': offering_name,
                'type': offering_type
            },
            'clients': clients,
            'total_clients': len(clients)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/revenue-breakdown', methods=['GET'])
@require_auth
def get_revenue_breakdown(current_user=None):
    """Get revenue breakdown by source"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)

        breakdown = {
            'service': 0,
            'product': 0,
            'package': 0,
            'prepaid': 0,
            'membership': 0
        }

        for bill in bills:
            for item in bill.items:
                if item.item_type in breakdown:
                    breakdown[item.item_type] += float(item.total) if item.total else 0.0

        total = sum(breakdown.values())

        return jsonify({
            'breakdown': {
                key: {
                    'amount': round(value, 2),
                    'percentage': round((value / total * 100) if total > 0 else 0, 2)
                }
                for key, value in breakdown.items()
            },
            'total': round(total, 2)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/payment-distribution', methods=['GET'])
@require_auth
def get_payment_distribution(current_user=None):
    """Get payment method breakdown"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        start, end = get_ist_date_range(start_date, end_date)

        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end,
            payment_mode__ne=None
        )
        
        # Apply branch filter
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills = list(bills_query)
        
        # Group by payment mode
        payment_stats = {}
        for bill in bills:
            mode = bill.payment_mode or 'unknown'
            if mode not in payment_stats:
                payment_stats[mode] = {'total_amount': 0.0, 'count': 0}
            payment_stats[mode]['total_amount'] += float(bill.final_amount) if bill.final_amount else 0.0
            payment_stats[mode]['count'] += 1
        
        total = sum([stats['total_amount'] for stats in payment_stats.values()])

        return jsonify({
            'distribution': [{
                'payment_mode': mode,
                'amount': round(stats['total_amount'], 2),
                'count': stats['count'],
                'percentage': round((stats['total_amount'] / total * 100) if total > 0 else 0, 2)
            } for mode, stats in payment_stats.items()],
            'total': round(total, 2)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/top-moving-items', methods=['GET'])
@require_auth
@cache_response(ttl=60)  # Cache for 60 seconds
@log_performance
def get_top_moving_items(current_user=None):
    """Get top moving items (services, packages, products) with trends and stock status - OPTIMIZED with aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        
        # Convert IST dates to UTC for filtering
        if start_date or end_date:
            start, end = get_ist_date_range(start_date, end_date)
        else:
            # Default to last 30 days (using IST)
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            default_end_date = today_ist
            start, end = get_ist_date_range(default_start_date, default_end_date)
        
        # Calculate previous period for trend comparison
        if start_date and end_date:
            # Calculate period length
            period_start = datetime.strptime(start_date, '%Y-%m-%d')
            period_end = datetime.strptime(end_date, '%Y-%m-%d')
            period_days = (period_end - period_start).days + 1
            prev_start_date = (period_start - timedelta(days=period_days)).strftime('%Y-%m-%d')
            prev_end_date = (period_start - timedelta(days=1)).strftime('%Y-%m-%d')
            prev_start, prev_end = get_ist_date_range(prev_start_date, prev_end_date)
        else:
            # Default: compare with previous 30 days (using IST)
            today_ist = get_ist_today()
            prev_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=60)
            prev_start_date = prev_start_date_obj.strftime('%Y-%m-%d')
            prev_end_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=31)
            prev_end_date = prev_end_date_obj.strftime('%Y-%m-%d')
            prev_start, prev_end = get_ist_date_range(prev_start_date, prev_end_date)
        
        # Build match stage for current period
        current_match = {
            "is_deleted": False,
            "bill_date": {"$gte": start, "$lte": end}
        }
        if branch:
            current_match["branch"] = ObjectId(str(branch.id))
        
        # Build match stage for previous period
        prev_match = {
            "is_deleted": False,
            "bill_date": {"$gte": prev_start, "$lte": prev_end}
        }
        if branch:
            prev_match["branch"] = ObjectId(str(branch.id))
        
        # OPTIMIZED: Aggregation pipeline for services (current period)
        # Uses denormalized 'name' field from bill items when available, falls back to service lookup
        services_current_pipeline = [
            {"$match": current_match},
            {"$unwind": "$items"},
            {"$match": {
                "items.item_type": "service",
                "items.service": {"$ne": None}
            }},
            {"$group": {
                "_id": "$items.service",
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "bills": {"$addToSet": "$_id"},
                # Get any non-null denormalized name from items ($max picks string over null)
                "item_name": {"$max": "$items.name"}
            }},
            # Handle DBRef: extract ObjectId from $id field if present
            {"$addFields": {
                "_id": {"$ifNull": ["$_id.$id", "$_id"]}
            }},
            {"$project": {
                "service_id": {"$toString": "$_id"},
                "raw_id": "$_id",
                "item_name": 1,
                "revenue": {"$round": ["$revenue", 2]},
                "bills_count": {"$size": "$bills"}
            }}
        ]

        # Aggregation pipeline for services (previous period)
        services_prev_pipeline = [
            {"$match": prev_match},
            {"$unwind": "$items"},
            {"$match": {
                "items.item_type": "service",
                "items.service": {"$ne": None}
            }},
            {"$group": {
                "_id": "$items.service",
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}}
            }},
            # Handle DBRef: extract ObjectId from $id field if present
            {"$addFields": {
                "_id": {"$ifNull": ["$_id.$id", "$_id"]}
            }},
            {"$project": {
                "service_id": {"$toString": "$_id"},
                "revenue": {"$round": ["$revenue", 2]}
            }}
        ]

        # Execute both pipelines
        services_current = list(Bill.objects.aggregate(services_current_pipeline))
        services_prev = list(Bill.objects.aggregate(services_prev_pipeline))

        # Fetch all service names at once using Python (as fallback for items without denormalized name)
        # First, collect service IDs that don't have denormalized names
        service_ids_needing_lookup = [s.get('raw_id') for s in services_current if s.get('raw_id') and not s.get('item_name')]
        service_name_map = {}
        if service_ids_needing_lookup:
            try:
                existing_services = Service.objects(id__in=service_ids_needing_lookup)
                for svc in existing_services:
                    service_name_map[str(svc.id)] = svc.name
            except Exception as e:
                print(f"[WARNING] Error fetching services: {e}")

        # Create lookup for previous period revenue
        prev_revenue_map = {s['service_id']: s['revenue'] for s in services_prev}

        # Calculate trends and build services list
        services_list = []
        for s in services_current:
            service_id = s.get('service_id')
            current_revenue = s.get('revenue', 0.0)
            prev_revenue = prev_revenue_map.get(service_id, 0.0)

            if prev_revenue == 0:
                trend = 'trending_up' if current_revenue > 0 else 'minus'
            elif current_revenue > prev_revenue * 1.1:  # 10% increase
                trend = 'trending_up'
            elif current_revenue < prev_revenue * 0.9:  # 10% decrease
                trend = 'trending_down'
            else:
                trend = 'minus'

            # Priority: 1) denormalized item_name, 2) service lookup, 3) fallback to 'Service'
            service_name = s.get('item_name') or service_name_map.get(service_id) or 'Service'

            services_list.append({
                'name': service_name,
                'bills': s.get('bills_count', 0),
                'revenue': current_revenue,
                'trend': trend
            })

        # Sort by revenue and limit to top 10
        services_list = sorted(services_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        # OPTIMIZED: Aggregation pipeline for packages (current period)
        # Uses denormalized 'name' field from bill items when available
        packages_current_pipeline = [
            {"$match": current_match},
            {"$unwind": "$items"},
            {"$match": {
                "items.item_type": "package",
                "items.package": {"$ne": None}
            }},
            {"$group": {
                "_id": "$items.package",
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "sold": {"$sum": {"$ifNull": ["$items.quantity", 1]}},
                # Get any non-null denormalized name from items ($max picks string over null)
                "item_name": {"$max": "$items.name"}
            }},
            # Handle DBRef: extract ObjectId from $id field if present
            {"$addFields": {
                "_id": {"$ifNull": ["$_id.$id", "$_id"]}
            }},
            {"$project": {
                "package_id": {"$toString": "$_id"},
                "raw_id": "$_id",
                "item_name": 1,
                "revenue": {"$round": ["$revenue", 2]},
                "sold": 1
            }}
        ]

        packages_current = list(Bill.objects.aggregate(packages_current_pipeline))

        # Fetch all package names at once using Python (as fallback for items without denormalized name)
        package_ids_needing_lookup = [p.get('raw_id') for p in packages_current if p.get('raw_id') and not p.get('item_name')]
        package_name_map = {}
        if package_ids_needing_lookup:
            try:
                existing_packages = Package.objects(id__in=package_ids_needing_lookup)
                for pkg in existing_packages:
                    package_name_map[str(pkg.id)] = pkg.name
            except Exception as e:
                print(f"[WARNING] Error fetching packages: {e}")

        # Calculate average sales for status
        if packages_current:
            avg_sales = sum(p.get('sold', 0) for p in packages_current) / len(packages_current)
        else:
            avg_sales = 0

        packages_list = []
        for p in packages_current:
            sold = p.get('sold', 0)
            if sold > avg_sales * 1.2:
                status = 'High Demand'
            elif sold < avg_sales * 0.8:
                status = 'Low Demand'
            else:
                status = 'Stable'

            # Priority: 1) denormalized item_name, 2) package lookup, 3) fallback to 'Package'
            package_name = p.get('item_name') or package_name_map.get(p.get('package_id')) or 'Package'

            packages_list.append({
                'name': package_name,
                'sold': sold,
                'revenue': p.get('revenue', 0.0),
                'status': status
            })

        # Sort by revenue and limit to top 10
        packages_list = sorted(packages_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        # OPTIMIZED: Aggregation pipeline for products (current period)
        # Uses denormalized 'name' field from bill items when available
        products_current_pipeline = [
            {"$match": current_match},
            {"$unwind": "$items"},
            {"$match": {
                "items.item_type": "product",
                "items.product": {"$ne": None}
            }},
            {"$group": {
                "_id": "$items.product",
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "sold": {"$sum": {"$ifNull": ["$items.quantity", 1]}},
                # Get any non-null denormalized name from items ($max picks string over null)
                "item_name": {"$max": "$items.name"}
            }},
            # Handle DBRef: extract ObjectId from $id field if present
            {"$addFields": {
                "_id": {"$ifNull": ["$_id.$id", "$_id"]}
            }},
            {"$project": {
                "product_id": {"$toString": "$_id"},
                "raw_id": "$_id",
                "item_name": 1,
                "revenue": {"$round": ["$revenue", 2]},
                "sold": 1
            }}
        ]

        products_current = list(Bill.objects.aggregate(products_current_pipeline))

        # Fetch all product info at once using Python (for items without denormalized name, and for stock info)
        product_ids = [p.get('raw_id') for p in products_current if p.get('raw_id')]
        product_info_map = {}
        if product_ids:
            try:
                existing_products = Product.objects(id__in=product_ids)
                for prod in existing_products:
                    product_info_map[str(prod.id)] = {
                        'name': prod.name,
                        'stock_quantity': prod.stock_quantity or 0,
                        'min_stock_level': prod.min_stock_level or 0
                    }
            except Exception as e:
                print(f"[WARNING] Error fetching products: {e}")

        products_list = []
        for p in products_current:
            product_id = p.get('product_id')
            product_info = product_info_map.get(product_id, {})

            stock_quantity = product_info.get('stock_quantity', 0)
            min_stock_level = product_info.get('min_stock_level', 0)

            stock_status = 'OK'
            if stock_quantity is not None and min_stock_level is not None:
                if stock_quantity <= min_stock_level:
                    stock_status = 'Low'

            # Priority: 1) denormalized item_name, 2) product lookup, 3) fallback to 'Product'
            product_name = p.get('item_name') or product_info.get('name') or 'Product'

            products_list.append({
                'name': product_name,
                'sold': p.get('sold', 0),
                'revenue': p.get('revenue', 0.0),
                'stock': stock_status
            })

        # Sort by revenue and limit to top 10
        products_list = sorted(products_list, key=lambda x: x['revenue'], reverse=True)[:10]
        
        return jsonify({
            'services': services_list,
            'packages': packages_list,
            'products': products_list
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD] Error in get_top_moving_items: {str(e)}")
        print(f"[DASHBOARD] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/client-funnel', methods=['GET'])
@require_auth
def get_client_funnel(current_user=None):
    """Get client acquisition funnel"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert IST dates to UTC for filtering
        if start_date:
            start = ist_to_utc_start(start_date)
        else:
            # Default to 30 days ago in IST, convert to UTC
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            start = ist_to_utc_start(default_start_date)

        if end_date:
            end = ist_to_utc_end(end_date)
        else:
            # Default to today in IST, convert to UTC
            end = ist_to_utc_end(get_ist_today())

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)

        # Total customers - filter by branch
        customers_query = Customer.objects
        if branch:
            customers_query = customers_query.filter(branch=branch)
        total_customers = customers_query.count()

        # New customers in period - filter by branch
        new_customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            new_customers_query = new_customers_query.filter(branch=branch)
        new_customers = new_customers_query.count()

        # Returning customers (with more than 1 bill) - filter by branch
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        bills_in_period = list(bills_query)
        customer_bill_count = {}
        for bill in bills_in_period:
            customer_info = get_safe_customer_info(bill.customer)
            if customer_info['id']:
                customer_id = customer_info['id']
                customer_bill_count[customer_id] = customer_bill_count.get(customer_id, 0) + 1
        returning_customers = len([cid for cid, count in customer_bill_count.items() if count > 1])

        # Leads
        total_leads = Lead.objects.count()
        converted_leads = Lead.objects(converted_to_customer=True).count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        return jsonify({
            'customers': {
                'total': total_customers,
                'new': new_customers,
                'returning': returning_customers
            },
            'leads': {
                'total': total_leads,
                'converted': converted_leads,
                'conversion_rate': round(conversion_rate, 2)
            }
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/client-source', methods=['GET'])
@require_auth
def get_client_source(current_user=None):
    """Get client source distribution"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert IST dates to UTC for filtering
        if start_date:
            start = ist_to_utc_start(start_date)
        else:
            # Default to 30 days ago in IST, convert to UTC
            today_ist = get_ist_today()
            default_start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            default_start_date = default_start_date_obj.strftime('%Y-%m-%d')
            start = ist_to_utc_start(default_start_date)

        if end_date:
            end = ist_to_utc_end(end_date)
        else:
            # Default to today in IST, convert to UTC
            end = ist_to_utc_end(get_ist_today())

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)

        # Get customers in date range - filter by branch
        customers_query = Customer.objects(
            created_at__gte=start,
            created_at__lte=end
        )
        if branch:
            customers_query = customers_query.filter(branch=branch)
        
        # Force evaluation by converting to list
        customers = list(customers_query)
        
        # Group by source
        source_stats = {}
        for customer in customers:
            source = customer.source or 'Unknown'
            if source not in source_stats:
                source_stats[source] = {
                    'count': 0,
                    'revenue': 0.0
                }
            source_stats[source]['count'] += 1
        
        # Calculate revenue per source from bills
        bills_query = Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        )
        if branch:
            bills_query = bills_query.filter(branch=branch)
        
        bills = list(bills_query)
        for bill in bills:
            customer_info = get_safe_customer_info(bill.customer)
            if customer_info['source']:
                source = customer_info['source']
                if source in source_stats:
                    source_stats[source]['revenue'] += float(bill.final_amount) if bill.final_amount else 0.0
        
        # Convert to list format
        distribution = []
        total_customers = sum(s['count'] for s in source_stats.values())
        total_revenue = sum(s['revenue'] for s in source_stats.values())
        
        for source, stats in source_stats.items():
            distribution.append({
                'source': source,
                'count': stats['count'],
                'revenue': round(stats['revenue'], 2),
                'percentage': round((stats['count'] / total_customers * 100) if total_customers > 0 else 0, 2)
            })
        
        # Sort by count descending
        distribution.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'distribution': distribution,
            'total_customers': total_customers,
            'total_revenue': round(total_revenue, 2)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
@require_auth
def get_operational_alerts(current_user=None):
    """Get operational alerts"""
    try:
        alerts = []

        # Low stock products - compare stock_quantity with min_stock_level for each product
        low_stock_products = 0
        try:
            all_products = Product.objects(status='active')
            for product in all_products:
                if product.stock_quantity is not None and product.min_stock_level is not None:
                    if product.stock_quantity <= product.min_stock_level:
                        low_stock_products += 1
        except Exception:
            low_stock_products = 0

        if low_stock_products > 0:
            alerts.append({
                'type': 'low_stock',
                'severity': 'warning',
                'message': f'{low_stock_products} product(s) are running low on stock',
                'count': low_stock_products
            })

        # Cancelled bills today (using IST)
        today_ist_str = get_ist_today()
        today_start, today_end = get_ist_date_range(today_ist_str, today_ist_str)
        cancelled_bills = Bill.objects(
            is_deleted=True,
            deleted_at__gte=today_start,
            deleted_at__lte=today_end
        ).count()

        if cancelled_bills > 0:
            alerts.append({
                'type': 'cancelled_bills',
                'severity': 'info',
                'message': f'{cancelled_bills} bill(s) cancelled today',
                'count': cancelled_bills
            })

        # No-show appointments today (using IST)
        today_ist_date = datetime.strptime(today_ist_str, '%Y-%m-%d').date()
        no_shows = Appointment.objects(
            appointment_date=today_ist_date,
            status='no-show'
        ).count()

        if no_shows > 0:
            alerts.append({
                'type': 'no_shows',
                'severity': 'warning',
                'message': f'{no_shows} no-show appointment(s) today',
                'count': no_shows
            })

        # Upcoming appointments today (using IST)
        upcoming = Appointment.objects(
            appointment_date=today_ist_date,
            status='confirmed'
        ).count()

        if upcoming > 0:
            alerts.append({
                'type': 'upcoming_appointments',
                'severity': 'info',
                'message': f'{upcoming} upcoming appointment(s) today',
                'count': upcoming
            })

        return jsonify(alerts)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD STATS] Error in get_staff_performance: {str(e)}")
        print(f"[DASHBOARD STATS] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/top-performer', methods=['GET'])
@require_auth
@cache_response(ttl=300)  # Cache for 5 minutes
@log_performance
def get_top_performer(current_user=None):
    """Calculate top performer based on weighted scoring system (company-wide) - OPTIMIZED with aggregation"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Default to last 30 days if no date range provided (using IST)
        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # OPTIMIZED: Single aggregation pipeline for all staff revenue and service metrics
        bills_pipeline = [
            {"$match": {
                "is_deleted": False,
                "bill_date": {"$gte": start, "$lte": end}
            }},
            {"$unwind": "$items"},
            {"$match": {"items.staff": {"$ne": None}}},
            {"$group": {
                "_id": "$items.staff",
                "revenue": {"$sum": {"$ifNull": ["$items.total", 0]}},
                "service_count": {
                    "$sum": {
                        "$cond": [
                            {"$in": [{"$ifNull": ["$items.item_type", "service"]}, ["service"]]},
                            {"$ifNull": ["$items.quantity", 1]},
                            0
                        ]
                    }
                },
                "customers": {"$addToSet": "$customer"}
            }},
            {"$lookup": {
                "from": "staffs",
                "localField": "_id",
                "foreignField": "_id",
                "as": "staff_doc"
            }},
            {"$unwind": {"path": "$staff_doc", "preserveNullAndEmptyArrays": True}},
            {"$match": {"staff_doc.status": "active"}},
            {"$project": {
                "staff_id": {"$toString": "$_id"},
                "staff_name": {
                    "$concat": [
                        {"$ifNull": ["$staff_doc.first_name", ""]},
                        " ",
                        {"$ifNull": ["$staff_doc.last_name", ""]}
                    ]
                },
                "revenue": {"$round": ["$revenue", 2]},
                "service_count": 1,
                "customer_count": {"$size": "$customers"},
                "customer_ids": "$customers"
            }}
        ]

        # Execute bills aggregation
        bills_results = list(Bill.objects.aggregate(bills_pipeline))
        
        if not bills_results:
            return jsonify({
                'top_performer': None,
                'leaderboard': []
            })

        # Get all staff IDs from results
        staff_ids = [ObjectId(r['staff_id']) for r in bills_results if r.get('staff_id')]
        
        # OPTIMIZED: Single aggregation for all appointments
        appt_start_datetime = start.replace(hour=0, minute=0, second=0, microsecond=0)
        appt_end_datetime = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        appt_pipeline = [
            {"$match": {
                "staff": {"$in": staff_ids},
                "appointment_date": {"$gte": appt_start_datetime, "$lte": appt_end_datetime},
                "status": "completed"
            }},
            {"$group": {
                "_id": "$staff",
                "count": {"$sum": 1}
            }}
        ]
        appt_results = list(Appointment.objects.aggregate(appt_pipeline))
        appt_counts = {str(r['_id']): r['count'] for r in appt_results}

        # OPTIMIZED: Single aggregation for all feedbacks
        feedback_pipeline = [
            {"$match": {
                "staff": {"$in": staff_ids},
                "created_at": {"$gte": start, "$lte": end}
            }},
            {"$group": {
                "_id": "$staff",
                "avg_rating": {"$avg": "$rating"},
                "count": {"$sum": 1},
                "total_rating": {"$sum": "$rating"}
            }}
        ]
        feedback_results = list(Feedback.objects.aggregate(feedback_pipeline))
        feedback_data = {}
        for r in feedback_results:
            staff_id_str = str(r['_id'])
            count = r.get('count', 0)
            avg_rating = float(r.get('avg_rating', 0)) if count > 0 else 0.0
            feedback_data[staff_id_str] = {
                'count': count,
                'avg_rating': avg_rating
            }

        # OPTIMIZED: Single aggregation for customer retention (count visits per staff-customer pair)
        retention_pipeline = [
            {"$match": {
                "is_deleted": False,
                "bill_date": {"$gte": start, "$lte": end},
                "customer": {"$ne": None}
            }},
            {"$unwind": "$items"},
            {"$match": {
                "items.staff": {"$ne": None},
                "items.staff": {"$in": staff_ids}
            }},
            {"$group": {
                "_id": {
                    "staff": "$items.staff",
                    "customer": "$customer"
                },
                "visit_count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.staff",
                "total_customers": {"$sum": 1},
                "repeat_customers": {
                    "$sum": {
                        "$cond": [{"$gte": ["$visit_count", 2]}, 1, 0]
                    }
                }
            }}
        ]
        retention_results = list(Bill.objects.aggregate(retention_pipeline))
        retention_data = {}
        for r in retention_results:
            staff_id_str = str(r['_id'])
            total = r.get('total_customers', 0)
            repeat = r.get('repeat_customers', 0)
            retention_rate = (repeat / total) if total > 0 else 0.0
            retention_data[staff_id_str] = {
                'total_customers': total,
                'repeat_customers': repeat,
                'retention_rate': retention_rate
            }

        # Calculate max values for normalization
        max_revenue = max((r.get('revenue', 0) for r in bills_results), default=1)
        max_services = max((r.get('service_count', 0) for r in bills_results), default=1)
        max_appts = max((appt_counts.get(r.get('staff_id', ''), 0) for r in bills_results), default=1)
        
        max_revenue = max_revenue if max_revenue > 0 else 1
        max_services = max_services if max_services > 0 else 1
        max_appts = max_appts if max_appts > 0 else 1

        # Calculate scores for each staff
        scores = []
        for r in bills_results:
            try:
                staff_id = r.get('staff_id', '')
                if not staff_id:
                    continue

                revenue = float(r.get('revenue', 0))
                service_count = int(r.get('service_count', 0))
                appointments = appt_counts.get(staff_id, 0)
                
                # Get feedback data
                feedback_info = feedback_data.get(staff_id, {'count': 0, 'avg_rating': 0.0})
                feedback_count = feedback_info['count']
                avg_rating = feedback_info['avg_rating']
                
                # Get retention data
                retention_info = retention_data.get(staff_id, {
                    'total_customers': 0,
                    'repeat_customers': 0,
                    'retention_rate': 0.0
                })
                retention_rate = retention_info['retention_rate']

                # Calculate weighted scores
                revenue_score = (revenue / max_revenue) * 40
                service_score = (service_count / max_services) * 20
                appt_score = (appointments / max_appts) * 15
                rating_score = (avg_rating / 5.0) * 15 if avg_rating > 0 else 0.0
                retention_score = retention_rate * 10

                total_score = revenue_score + service_score + appt_score + rating_score + retention_score

                scores.append({
                    'staff_id': staff_id,
                    'staff_name': r.get('staff_name', '').strip(),
                    'performance_score': round(float(total_score), 1),
                    'revenue': round(float(revenue), 2),
                    'service_count': int(service_count),
                    'completed_appointments': int(appointments),
                    'avg_rating': round(float(avg_rating), 2),
                    'feedback_count': int(feedback_count),
                    'retention_rate': round(float(retention_rate) * 100, 1)
                })
            except Exception as staff_error:
                print(f"Warning: Failed to compute score for staff {r.get('staff_id', 'unknown')}: {staff_error}")
                continue

        # Sort by performance score
        scores.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return jsonify({
            'top_performer': scores[0] if scores else None,
            'leaderboard': scores
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD] Error in get_top_performer: {str(e)}")
        print(f"[DASHBOARD] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

@dashboard_bp.route('/staff-leaderboard', methods=['GET'])
@require_auth
@cache_response(ttl=300)  # Cache for 5 minutes
@log_performance
def get_staff_leaderboard(current_user=None):
    """Get staff leaderboard (company-wide) - returns leaderboard using same logic as top-performer"""
    try:
        # Use same date range logic as top-performer
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today_ist = get_ist_today()
            start_date_obj = datetime.strptime(today_ist, '%Y-%m-%d') - timedelta(days=30)
            start_date = start_date_obj.strftime('%Y-%m-%d')
        if not end_date:
            end_date = get_ist_today()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get ALL active staff (company-wide, not filtered by branch)
        staff_list = list(Staff.objects(status='active'))
        
        if not staff_list:
            return jsonify({'leaderboard': []})
        
        # Get ALL bills in date range (company-wide, not filtered by branch)
        bills = list(Bill.objects(
            is_deleted=False,
            bill_date__gte=start,
            bill_date__lte=end
        ))
        
        def safe_get_staff_id(item_staff):
            """Safely get staff ID from a staff reference"""
            if not item_staff:
                return None
            try:
                if hasattr(item_staff, 'id'):
                    try:
                        return str(item_staff.id)
                    except (AttributeError, DoesNotExist):
                        if hasattr(item_staff, 'pk'):
                            return str(item_staff.pk)
                        return None
                elif isinstance(item_staff, str):
                    return item_staff
                elif hasattr(item_staff, '__str__'):
                    try:
                        return str(item_staff)
                    except:
                        return None
            except (AttributeError, DoesNotExist, TypeError, ValueError):
                return None
            return None
        
        # Calculate max values for normalization (same as top-performer)
        max_revenue = 0
        max_services = 0
        max_appts = 0
        
        for staff in staff_list:
            try:
                staff_id = str(staff.id)
                revenue = 0
                service_count = 0
                for bill in bills:
                    for item in (bill.items or []):
                        try:
                            item_staff_id = safe_get_staff_id(item.staff)
                            if item_staff_id and item_staff_id == staff_id:
                                revenue += float(item.total) if item.total else 0.0
                                service_count += int(item.quantity) if item.quantity else 1
                        except (AttributeError, TypeError, ValueError, DoesNotExist):
                            continue
                
                appointments = Appointment.objects(
                    staff=staff,
                    appointment_date__gte=start.date(),
                    appointment_date__lte=end.date(),
                    status='completed'
                ).count()
                
                max_revenue = max(max_revenue, revenue)
                max_services = max(max_services, service_count)
                max_appts = max(max_appts, appointments)
            except Exception:
                continue
        
        max_revenue = max_revenue if max_revenue > 0 else 1
        max_services = max_services if max_services > 0 else 1
        max_appts = max_appts if max_appts > 0 else 1
        
        scores = []
        
        for staff in staff_list:
            try:
                staff_id = str(staff.id)
                
                # Calculate revenue and service count
                revenue = 0
                service_count = 0
                customer_visits = {}
                
                for bill in bills:
                    for item in (bill.items or []):
                        try:
                            item_staff_id = safe_get_staff_id(item.staff)
                            if item_staff_id and item_staff_id == staff_id:
                                revenue += float(item.total) if item.total else 0.0
                                service_count += int(item.quantity) if item.quantity else 1
                                
                                customer_info = get_safe_customer_info(bill.customer)
                                if customer_info['id']:
                                    customer_id = customer_info['id']
                                    if customer_id not in customer_visits:
                                        customer_visits[customer_id] = 0
                                    customer_visits[customer_id] += 1
                        except (AttributeError, TypeError, ValueError, DoesNotExist):
                            continue
                
                revenue_score = (revenue / max_revenue) * 40
                service_score = (service_count / max_services) * 20
                
                appointments = Appointment.objects(
                    staff=staff,
                    appointment_date__gte=start.date(),
                    appointment_date__lte=end.date(),
                    status='completed'
                ).count()
                appt_score = (appointments / max_appts) * 15
                
                feedbacks = list(Feedback.objects(
                    staff=staff,
                    created_at__gte=start,
                    created_at__lte=end
                ))
                feedback_count = len(feedbacks)
                if feedback_count > 0:
                    total_rating = sum(float(f.rating) for f in feedbacks if f.rating is not None)
                    avg_rating = total_rating / feedback_count if feedback_count > 0 else 0.0
                    rating_score = (avg_rating / 5.0) * 15 if avg_rating > 0 else 0.0
                else:
                    avg_rating = 0.0
                    rating_score = 0.0
                
                total_customers = len(customer_visits)
                repeat_customers = sum(1 for visits in customer_visits.values() if visits >= 2)
                retention_rate = (repeat_customers / total_customers) if total_customers > 0 else 0
                retention_score = retention_rate * 10
                
                total_score = revenue_score + service_score + appt_score + rating_score + retention_score
                
                scores.append({
                    'staff_id': staff_id,
                    'staff_name': f"{staff.first_name or ''} {staff.last_name or ''}".strip(),
                    'performance_score': round(float(total_score), 1),
                    'revenue': round(float(revenue), 2),
                    'service_count': int(service_count),
                    'completed_appointments': int(appointments),
                    'avg_rating': round(float(avg_rating), 2),
                    'feedback_count': int(feedback_count),
                    'retention_rate': round(float(retention_rate) * 100, 1)
                })
            except Exception as staff_error:
                print(f"Warning: Failed to compute score for staff {getattr(staff, 'id', 'unknown')}: {staff_error}")
                continue
        
        scores.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return jsonify({
            'leaderboard': scores
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[DASHBOARD] Error in get_staff_leaderboard: {str(e)}")
        print(f"[DASHBOARD] Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500
