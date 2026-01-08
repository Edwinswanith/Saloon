from flask import Blueprint, jsonify, request
from models import Bill, Service, Product, ServiceGroup, ProductCategory
from datetime import datetime, timedelta
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.date_utils import get_ist_date_range
from utils.auth import require_auth

service_product_bp = Blueprint('service_product', __name__)

def handle_preflight():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Branch-Id')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@service_product_bp.route('/api/analytics/service-product-performance', methods=['OPTIONS'])
def service_product_performance_preflight():
    return handle_preflight()

@service_product_bp.route('/api/analytics/service-product-performance', methods=['GET'])
@require_auth
def service_product_performance(current_user=None):
    """Get service and product performance analytics with MongoDB aggregations"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        category_filter = request.args.get('category', 'all')
        type_filter = request.args.get('type', 'all')

        branch = get_selected_branch(request, current_user)
        branch_id = str(branch.id) if branch else None

        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=365)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')

        start_utc, end_utc = get_ist_date_range(start_date, end_date)

        match_stage = {
            'is_deleted': False,
            'bill_date': {'$gte': start_utc, '$lte': end_utc}
        }
        
        if branch_id and ObjectId.is_valid(branch_id):
            match_stage['branch'] = ObjectId(branch_id)

        service_pipeline = [
            {'$match': match_stage},
            {'$unwind': '$items'},
            {'$match': {
                'items.item_type': 'service',
                'items.service': {'$exists': True, '$ne': None}
            }},
            {'$addFields': {
                'serviceId': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$items.service'}, 'object']},  # DBRef is an object
                        'then': {
                            '$cond': {
                                'if': {'$ifNull': ['$items.service.$id', False]},  # Check if it's a DBRef with $id
                                'then': '$items.service.$id',  # Extract $id from DBRef
                                'else': '$items.service'  # Fallback
                            }
                        },
                        'else': {
                            '$cond': {
                                'if': {'$eq': [{'$type': '$items.service'}, 'string']},
                                'then': {
                                    '$cond': {
                                        'if': {'$eq': [{'$strLenCP': '$items.service'}, 24]},
                                        'then': {'$toObjectId': '$items.service'},
                                        'else': '$items.service'
                                    }
                                },
                                'else': '$items.service'  # Already ObjectId
                            }
                        }
                    }
                }
            }},
            {'$lookup': {
                'from': 'services',
                'localField': 'serviceId',
                'foreignField': '_id',
                'as': 'serviceDetails'
            }},
            {'$unwind': {'path': '$serviceDetails', 'preserveNullAndEmptyArrays': True}},
            {'$addFields': {
                'groupId': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$serviceDetails.group'}, 'object']},  # DBRef is an object
                        'then': {
                            '$cond': {
                                'if': {'$ifNull': ['$serviceDetails.group.$id', False]},  # Check if it's a DBRef with $id
                                'then': '$serviceDetails.group.$id',  # Extract $id from DBRef
                                'else': '$serviceDetails.group'  # Fallback
                            }
                        },
                        'else': {
                            '$cond': {
                                'if': {'$and': [
                                    {'$ne': ['$serviceDetails.group', None]},
                                    {'$eq': [{'$type': '$serviceDetails.group'}, 'string']}
                                ]},
                                'then': {'$toObjectId': '$serviceDetails.group'},
                                'else': '$serviceDetails.group'  # Already ObjectId
                            }
                        }
                    }
                }
            }},
            {'$lookup': {
                'from': 'service_groups',
                'localField': 'groupId',
                'foreignField': '_id',
                'as': 'groupDetails'
            }},
            {'$unwind': {'path': '$groupDetails', 'preserveNullAndEmptyArrays': True}},
            {'$group': {
                '_id': '$serviceId',
                'serviceId': {'$first': {'$toString': '$serviceId'}},
                'serviceName': {'$first': {'$ifNull': ['$serviceDetails.name', 'Unknown Service']}},
                'category': {'$first': {'$ifNull': ['$groupDetails.name', 'Uncategorized']}},
                'totalBookings': {'$sum': {'$ifNull': ['$items.quantity', 1]}},
                'totalRevenue': {'$sum': {'$ifNull': ['$items.total', 0]}},
                'avgPrice': {'$avg': {'$ifNull': ['$items.price', 0]}}
            }},
            {'$sort': {'totalRevenue': -1}}
        ]

        if category_filter != 'all' and type_filter in ['all', 'services']:
            service_pipeline.insert(-2, {
                '$match': {
                    '$or': [
                        {'groupDetails.name': category_filter},
                        {'$and': [
                            {'$or': [
                                {'groupDetails': None},
                                {'groupDetails.name': {'$exists': False}}
                            ]},
                            {'$expr': {'$eq': [{'$literal': category_filter}, 'Uncategorized']}}
                        ]}
                    ]
                }
            })

        service_results_raw = list(Bill.objects.aggregate(service_pipeline))
        
        # Post-process to resolve service names and categories using MongoEngine
        service_results = []
        for result in service_results_raw:
            service_id_raw = result.get('_id')
            if not service_id_raw:
                continue
                
            service_id = None
            service_name = 'Unknown Service'
            category = 'Uncategorized'
            
            try:
                # Handle different formats: DBRef dict, ObjectId, string
                if isinstance(service_id_raw, dict):
                    # It's a DBRef or dict, extract the ID
                    if '$id' in service_id_raw:
                        service_id = service_id_raw['$id']
                    elif 'id' in service_id_raw:
                        service_id = service_id_raw['id']
                    else:
                        print(f"Unexpected dict format for service_id_raw: {service_id_raw}")
                        continue
                elif isinstance(service_id_raw, ObjectId):
                    service_id = service_id_raw
                elif isinstance(service_id_raw, str):
                    try:
                        service_id = ObjectId(service_id_raw)
                    except:
                        print(f"Invalid ObjectId string: {service_id_raw}")
                        continue
                else:
                    # Try to convert to ObjectId
                    try:
                        service_id = ObjectId(str(service_id_raw))
                    except:
                        print(f"Could not convert service_id_raw to ObjectId: {service_id_raw} (type: {type(service_id_raw)})")
                        continue
                
                # Now query the service using MongoEngine (handles ReferenceFields properly)
                if service_id:
                    service_obj = Service.objects(id=service_id).first()
                    if service_obj:
                        service_name = service_obj.name
                        # Get service group
                        if service_obj.group:
                            try:
                                # Reload to ensure group is dereferenced
                                if hasattr(service_obj.group, 'reload'):
                                    service_obj.group.reload()
                                if hasattr(service_obj.group, 'name'):
                                    category = service_obj.group.name
                                else:
                                    # Try to get group directly
                                    group_obj = ServiceGroup.objects(id=service_obj.group.id).first() if hasattr(service_obj.group, 'id') else None
                                    if group_obj:
                                        category = group_obj.name
                            except Exception as group_error:
                                print(f"Error getting group for service {service_id}: {group_error}")
                                category = 'Uncategorized'
                    else:
                        print(f"Service not found for ID: {service_id} (raw: {service_id_raw})")
            except Exception as e:
                print(f"Error resolving service {service_id_raw}: {e}")
                import traceback
                traceback.print_exc()
            
            # Build result with resolved names
            service_results.append({
                'serviceId': str(service_id) if service_id else str(service_id_raw),
                'serviceName': service_name,
                'category': category,
                'totalBookings': int(result.get('totalBookings', 0)),
                'totalRevenue': float(result.get('totalRevenue', 0)),
                'avgPrice': float(result.get('avgPrice', 0))
            })

        product_pipeline = [
            {'$match': match_stage},
            {'$unwind': '$items'},
            {'$match': {
                'items.item_type': 'product',
                'items.product': {'$exists': True, '$ne': None}
            }},
            {'$addFields': {
                'productId': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$items.product'}, 'object']},  # DBRef is an object
                        'then': {
                            '$cond': {
                                'if': {'$ifNull': ['$items.product.$id', False]},  # Check if it's a DBRef with $id
                                'then': '$items.product.$id',  # Extract $id from DBRef
                                'else': '$items.product'  # Fallback
                            }
                        },
                        'else': {
                            '$cond': {
                                'if': {'$eq': [{'$type': '$items.product'}, 'string']},
                                'then': {
                                    '$cond': {
                                        'if': {'$eq': [{'$strLenCP': '$items.product'}, 24]},
                                        'then': {'$toObjectId': '$items.product'},
                                        'else': '$items.product'
                                    }
                                },
                                'else': '$items.product'  # Already ObjectId
                            }
                        }
                    }
                }
            }},
            {'$lookup': {
                'from': 'products',
                'localField': 'productId',
                'foreignField': '_id',
                'as': 'productDetails'
            }},
            {'$unwind': {'path': '$productDetails', 'preserveNullAndEmptyArrays': True}},
            {'$addFields': {
                'categoryId': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$productDetails.category'}, 'object']},  # DBRef is an object
                        'then': {
                            '$cond': {
                                'if': {'$ifNull': ['$productDetails.category.$id', False]},  # Check if it's a DBRef with $id
                                'then': '$productDetails.category.$id',  # Extract $id from DBRef
                                'else': '$productDetails.category'  # Fallback
                            }
                        },
                        'else': {
                            '$cond': {
                                'if': {'$and': [
                                    {'$ne': ['$productDetails.category', None]},
                                    {'$eq': [{'$type': '$productDetails.category'}, 'string']}
                                ]},
                                'then': {'$toObjectId': '$productDetails.category'},
                                'else': '$productDetails.category'  # Already ObjectId
                            }
                        }
                    }
                }
            }},
            {'$lookup': {
                'from': 'product_categories',
                'localField': 'categoryId',
                'foreignField': '_id',
                'as': 'categoryDetails'
            }},
            {'$unwind': {'path': '$categoryDetails', 'preserveNullAndEmptyArrays': True}},
            {'$group': {
                '_id': '$productId',
                'productId': {'$first': {'$toString': '$productId'}},
                'productName': {'$first': {'$ifNull': ['$productDetails.name', 'Unknown Product']}},
                'category': {'$first': {'$ifNull': ['$categoryDetails.name', 'Uncategorized']}},
                'unitsSold': {'$sum': {'$ifNull': ['$items.quantity', 1]}},
                'totalRevenue': {'$sum': {'$ifNull': ['$items.total', 0]}},
                'stockQuantity': {'$first': {'$ifNull': ['$productDetails.stock_quantity', 0]}}
            }},
            {'$sort': {'totalRevenue': -1}}
        ]

        if category_filter != 'all' and type_filter in ['all', 'products']:
            product_pipeline.insert(-2, {
                '$match': {
                    '$or': [
                        {'categoryDetails.name': category_filter},
                        {'$and': [
                            {'$or': [
                                {'categoryDetails': None},
                                {'categoryDetails.name': {'$exists': False}}
                            ]},
                            {'$expr': {'$eq': [{'$literal': category_filter}, 'Uncategorized']}}
                        ]}
                    ]
                }
            })

        product_results_raw = list(Bill.objects.aggregate(product_pipeline))
        
        # Post-process to resolve product names and categories using MongoEngine
        product_results = []
        for result in product_results_raw:
            product_id_raw = result.get('_id')
            if not product_id_raw:
                continue
                
            product_id = None
            product_name = 'Unknown Product'
            category = 'Uncategorized'
            stock_quantity = 0
            
            try:
                # Handle different formats: DBRef dict, ObjectId, string
                if isinstance(product_id_raw, dict):
                    # It's a DBRef or dict, extract the ID
                    if '$id' in product_id_raw:
                        product_id = product_id_raw['$id']
                    elif 'id' in product_id_raw:
                        product_id = product_id_raw['id']
                    else:
                        print(f"Unexpected dict format for product_id_raw: {product_id_raw}")
                        continue
                elif isinstance(product_id_raw, ObjectId):
                    product_id = product_id_raw
                elif isinstance(product_id_raw, str):
                    try:
                        product_id = ObjectId(product_id_raw)
                    except:
                        print(f"Invalid ObjectId string: {product_id_raw}")
                        continue
                else:
                    # Try to convert to ObjectId
                    try:
                        product_id = ObjectId(str(product_id_raw))
                    except:
                        print(f"Could not convert product_id_raw to ObjectId: {product_id_raw} (type: {type(product_id_raw)})")
                        continue
                
                # Now query the product using MongoEngine (handles ReferenceFields properly)
                if product_id:
                    product_obj = Product.objects(id=product_id).first()
                    if product_obj:
                        product_name = product_obj.name
                        stock_quantity = product_obj.stock_quantity if hasattr(product_obj, 'stock_quantity') else 0
                        # Get product category
                        if product_obj.category:
                            try:
                                # Reload to ensure category is dereferenced
                                if hasattr(product_obj.category, 'reload'):
                                    product_obj.category.reload()
                                if hasattr(product_obj.category, 'name'):
                                    category = product_obj.category.name
                                else:
                                    # Try to get category directly
                                    category_obj = ProductCategory.objects(id=product_obj.category.id).first() if hasattr(product_obj.category, 'id') else None
                                    if category_obj:
                                        category = category_obj.name
                            except Exception as cat_error:
                                print(f"Error getting category for product {product_id}: {cat_error}")
                                category = 'Uncategorized'
                    else:
                        print(f"Product not found for ID: {product_id} (raw: {product_id_raw})")
            except Exception as e:
                print(f"Error resolving product {product_id_raw}: {e}")
                import traceback
                traceback.print_exc()
            
            # Build result with resolved names
            product_results.append({
                'productId': str(product_id) if product_id else str(product_id_raw),
                'productName': product_name,
                'category': category,
                'unitsSold': int(result.get('unitsSold', 0)),
                'totalRevenue': float(result.get('totalRevenue', 0)),
                'stockQuantity': int(stock_quantity)
            })

        total_service_revenue = sum(float(s.get('totalRevenue', 0)) for s in service_results)
        total_product_revenue = sum(float(p.get('totalRevenue', 0)) for p in product_results)
        total_units_sold = sum(int(p.get('unitsSold', 0)) for p in product_results)
        
        service_count = len(service_results)
        product_count = len(product_results)
        
        avg_revenue_per_service = total_service_revenue / service_count if service_count > 0 else 0
        avg_revenue_per_product = total_product_revenue / product_count if product_count > 0 else 0

        for service in service_results:
            service_revenue = float(service.get('totalRevenue', 0))
            contribution = (service_revenue / total_service_revenue * 100) if total_service_revenue > 0 else 0
            service['contribution'] = round(contribution, 2)

        service_categories = {}
        for service in service_results:
            cat = service.get('category', 'Uncategorized')
            if cat not in service_categories:
                service_categories[cat] = {'revenue': 0, 'count': 0}
            service_categories[cat]['revenue'] += float(service.get('totalRevenue', 0))
            service_categories[cat]['count'] += 1

        product_categories = {}
        for product in product_results:
            cat = product.get('category', 'Uncategorized')
            if cat not in product_categories:
                product_categories[cat] = {'revenue': 0, 'count': 0}
            product_categories[cat]['revenue'] += float(product.get('totalRevenue', 0))
            product_categories[cat]['count'] += 1

        total_category_revenue = sum(c['revenue'] for c in service_categories.values()) + \
                                 sum(c['revenue'] for c in product_categories.values())

        service_category_list = [
            {
                'category': cat,
                'revenue': round(data['revenue'], 2),
                'count': data['count'],
                'percentage': round((data['revenue'] / total_category_revenue * 100) if total_category_revenue > 0 else 0, 2),
                'type': 'service'
            }
            for cat, data in service_categories.items()
        ]

        product_category_list = [
            {
                'category': cat,
                'revenue': round(data['revenue'], 2),
                'count': data['count'],
                'percentage': round((data['revenue'] / total_category_revenue * 100) if total_category_revenue > 0 else 0, 2),
                'type': 'product'
            }
            for cat, data in product_categories.items()
        ]

        service_category_list.sort(key=lambda x: x['revenue'], reverse=True)
        product_category_list.sort(key=lambda x: x['revenue'], reverse=True)

        services_formatted = []
        for s in service_results:
            services_formatted.append({
                'id': s.get('serviceId', ''),
                'name': s.get('serviceName', 'Unknown Service'),
                'category': s.get('category', 'Uncategorized'),
                'totalBookings': int(s.get('totalBookings', 0)),
                'totalRevenue': round(float(s.get('totalRevenue', 0)), 2),
                'avgPrice': round(float(s.get('avgPrice', 0)), 2),
                'contribution': s.get('contribution', 0)
            })

        products_formatted = []
        for p in product_results:
            products_formatted.append({
                'id': p.get('productId', ''),
                'name': p.get('productName', 'Unknown Product'),
                'category': p.get('category', 'Uncategorized'),
                'unitsSold': int(p.get('unitsSold', 0)),
                'totalRevenue': round(float(p.get('totalRevenue', 0)), 2),
                'stockQuantity': int(p.get('stockQuantity', 0))
            })

        response_data = {
            'summary': {
                'totalServiceRevenue': round(total_service_revenue, 2),
                'totalProductRevenue': round(total_product_revenue, 2),
                'totalUnitsSold': total_units_sold,
                'avgRevenuePerService': round(avg_revenue_per_service, 2),
                'avgRevenuePerProduct': round(avg_revenue_per_product, 2)
            },
            'services': services_formatted,
            'products': products_formatted,
            'categories': {
                'services': service_category_list,
                'products': product_category_list
            }
        }

        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"Error in service_product_performance: {str(e)}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

