from flask import Blueprint, request, jsonify
from models import (
    Customer,
    Bill,
    OfferCampaign,
    WhatsAppMessage,
    WhatsAppWebhookEvent,
)
from datetime import datetime, timedelta
from bson import ObjectId
from mongoengine.errors import NotUniqueError
from utils.auth import get_current_user, require_auth, require_role
from utils.branch_filter import apply_branch_scope, apply_branch_scope_to_match, get_selected_branch
from utils.campaign_whatsapp import (
    CAMPAIGN_TEMPLATE_LANGUAGE,
    CAMPAIGN_TEMPLATE_NAME,
    build_campaign_request_hash,
    campaign_batch_size,
    campaign_error_requires_pause,
    campaign_flag_enabled,
    claim_campaign,
    claim_queued_recipient,
    expire_ambiguous_recipient_claims,
    normalize_indian_campaign_phone,
    pause_campaign,
    refresh_campaign_aggregates,
    release_campaign_lease,
    reserve_campaign_recipients,
    resume_campaign,
    set_recipient_status,
    update_campaign_recipient_status,
)
from utils.env_config import RuntimeConfigurationError, get_app_runtime
from utils.meta_whatsapp_service import (
    MetaWhatsAppError,
    MetaWhatsAppService,
    SALON_PRODUCTION_WABA_ID,
    sanitize_meta_error_text,
)
from services.r2_media_service import R2MediaError
from routes.whatsapp_integration_routes import (
    _enforce_send_rate_limits,
    _find_scoped_media_asset,
    _media_scope,
    _production_template_image,
    _read_stored_image,
    _store_whatsapp_media_upload,
)
from utils.branch_filter import is_demo_branch
from models import to_dict
import hmac
import os
import uuid

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


def _customer_name(customer):
    return f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'N/A'


def _bill_stats_by_customer(customer_ids, branch, current_user=None):
    if not customer_ids:
        return {}

    match_stage = {
        "customer": {"$in": [ObjectId(str(cid)) for cid in customer_ids]},
        "is_deleted": False
    }
    apply_branch_scope_to_match(match_stage, branch, current_user)

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$customer",
            "total_revenue": {"$sum": {"$ifNull": ["$final_amount", 0]}},
            "total_visits": {"$sum": 1},
            "last_visit": {"$max": "$bill_date"}
        }}
    ]

    return {
        str(row["_id"]): {
            "total_revenue": row.get("total_revenue", 0.0) or 0.0,
            "total_visits": row.get("total_visits", 0) or 0,
            "last_visit": row.get("last_visit")
        }
        for row in Bill.objects.aggregate(pipeline)
        if row.get("_id")
    }


def _campaign_customer_payload(customer, stats=None):
    stats = stats or {}
    return {
        'id': str(customer.id),
        'name': _customer_name(customer),
        'mobile': customer.mobile,
        'total_revenue': stats.get('total_revenue', 0.0),
        'total_visits': stats.get('total_visits', 0),
        'whatsapp_consent': customer.whatsapp_consent or False
    }


def _doc_or_id_to_string(value):
    try:
        if hasattr(value, 'id'):
            return str(value.id)
        return str(value)
    except Exception:
        return ''


def get_filtered_customers(filter_type, branch, current_user=None):
    """Get customers based on filter type, including ineligible rows for a clear preview."""
    base_query = Customer.objects(merged_into=None)
    base_query = apply_branch_scope(base_query, branch, current_user)
    
    if filter_type == 'all':
        customers = list(base_query)
        stats_map = _bill_stats_by_customer([c.id for c in customers], branch, current_user)
        return [
            _campaign_customer_payload(customer, stats_map.get(str(customer.id)))
            for customer in customers
        ]
    
    elif filter_type == 'top10_revenue':
        # Get top 10 by revenue
        match_stage = {"is_deleted": False}
        apply_branch_scope_to_match(match_stage, branch, current_user)
        
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
        stats_map = _bill_stats_by_customer([c.id for c in customers], branch, current_user)
        result = []
        for customer in customers:
            revenue_dict = {str(item['_id']): item['total_revenue'] for item in top_customers}
            stats = stats_map.get(str(customer.id), {})
            stats['total_revenue'] = revenue_dict.get(str(customer.id), 0.0)
            result.append(_campaign_customer_payload(customer, stats))
        # Sort by revenue descending
        result.sort(key=lambda x: x['total_revenue'], reverse=True)
        return result
    
    elif filter_type == 'top10_visits':
        # Get top 10 by visits
        match_stage = {"is_deleted": False}
        apply_branch_scope_to_match(match_stage, branch, current_user)
        
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
        stats_map = _bill_stats_by_customer([c.id for c in customers], branch, current_user)
        result = []
        for customer in customers:
            visits_dict = {str(item['_id']): item['total_visits'] for item in top_customers}
            stats = stats_map.get(str(customer.id), {})
            stats['total_visits'] = visits_dict.get(str(customer.id), 0)
            result.append(_campaign_customer_payload(customer, stats))
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
        recent_bills_query = apply_branch_scope(
            Bill.objects(is_deleted=False, bill_date__gte=cutoff_date),
            branch,
            current_user
        )
        recent_bills = recent_bills_query.distinct('customer')
        all_bills_query = apply_branch_scope(Bill.objects(is_deleted=False), branch, current_user)
        all_customers_with_bills = all_bills_query.distinct('customer')

        recent_customer_ids = {_doc_or_id_to_string(c) for c in recent_bills}
        inactive_customer_ids = [
            ObjectId(customer_id)
            for customer_id in (_doc_or_id_to_string(c) for c in all_customers_with_bills)
            if ObjectId.is_valid(customer_id) and customer_id not in recent_customer_ids
        ]
        customers = list(base_query.filter(id__in=inactive_customer_ids))
    else:
        customers = list(base_query)
    
    # For non-top10 filters, calculate stats in one grouped query.
    stats_map = _bill_stats_by_customer([c.id for c in customers], branch, current_user)
    return [
        _campaign_customer_payload(customer, stats_map.get(str(customer.id)))
        for customer in customers
    ]

@campaign_bp.route('/customers', methods=['GET'])
@require_role('manager', 'owner')
def get_campaign_customers(current_user=None):
    """Get filtered customer list for campaign targeting"""
    try:
        filter_type = request.args.get('filter', 'all')
        branch = get_selected_branch(request, current_user)
        customers = get_filtered_customers(filter_type, branch, current_user)
        
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
        
        # Use aggregation pipeline since MongoEngine doesn't support __month on date fields
        match_stage = {
            "merged_into": None,
            "dob": {"$exists": True, "$ne": None}
        }
        apply_branch_scope_to_match(match_stage, branch, current_user)

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

@campaign_bp.route('/media', methods=['POST'])
@require_role('manager', 'owner')
def upload_campaign_media(current_user=None):
    """Upload private campaign media without widening the Owner integration panel."""
    try:
        if get_app_runtime() != 'production':
            return jsonify({
                'error': 'Production campaign media is unavailable in this runtime.',
                'error_code': 'production_runtime_required',
            }), 403
    except RuntimeConfigurationError:
        return jsonify({
            'error': 'Application runtime is not configured.',
            'error_code': 'runtime_invalid',
        }), 503

    branch = get_selected_branch(request, current_user)
    if is_demo_branch(branch):
        return jsonify({
            'error': 'Production campaign media is unavailable for this branch.',
            'error_code': 'production_runtime_required',
        }), 403
    if not campaign_flag_enabled('WHATSAPP_PRODUCTION_SEND_ENABLED'):
        return jsonify({'error': 'Production sending is disabled.', 'error_code': 'send_disabled'}), 403
    if not campaign_flag_enabled('WHATSAPP_CAMPAIGN_SEND_ENABLED'):
        return jsonify({'error': 'Campaign sending is disabled.', 'error_code': 'campaign_disabled'}), 403
    return _store_whatsapp_media_upload(current_user)


@campaign_bp.route('/send', methods=['POST'])
@require_role('manager', 'owner')
def send_campaign(current_user=None):
    """Log a legacy manual campaign or queue a consented Cloud API campaign."""
    try:
        data = request.get_json(silent=True) or {}
        if not data.get('message_text'):
            response = jsonify({'error': 'Message text is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        branch = get_selected_branch(request, current_user)
        filter_type = data.get('filter_type', 'all')
        customer_ids = data.get('customer_ids', [])
        delivery_method = data.get('delivery_method', 'api')
        if customer_ids and not isinstance(customer_ids, list):
            return jsonify({'error': 'customer_ids must be an array.'}), 400

        if customer_ids:
            requested_ids = list(dict.fromkeys(
                str(customer_id) for customer_id in customer_ids if customer_id is not None
            ))
            valid_ids = [customer_id for customer_id in requested_ids if ObjectId.is_valid(customer_id)]
            customers_query = Customer.objects(id__in=valid_ids, merged_into=None)
            customers = list(apply_branch_scope(customers_query, branch, current_user))
        else:
            if delivery_method == 'api':
                return jsonify({
                    'error': 'Select explicit customers for a production API campaign.',
                    'error_code': 'campaign_recipients_required',
                }), 400
            customers_data = get_filtered_customers(filter_type, branch, current_user)
            requested_ids = [customer['id'] for customer in customers_data]
            customers_query = Customer.objects(id__in=requested_ids, merged_into=None)
            customers = list(apply_branch_scope(customers_query, branch, current_user))

        if delivery_method == 'direct_whatsapp' and not customers:
            response = jsonify({'error': 'No customers found to send campaign to'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if delivery_method == 'direct_whatsapp':
            return _log_direct_campaign(
                data, current_user, branch, filter_type, customers, requested_ids
            )
        if delivery_method != 'api':
            return jsonify({'error': 'Unsupported campaign delivery method.'}), 400
        return _send_meta_campaign(
            data, current_user, branch, filter_type, customers, requested_ids
        )
    except Exception:
        response = jsonify({'error': 'Campaign processing failed.'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


def _campaign_summary(campaign, *, duplicate=False):
    return {
        'campaign_id': str(campaign.id),
        'duplicate': duplicate,
        'requested_count': int(campaign.requested_count or 0),
        'eligible_count': int(campaign.eligible_count or 0),
        'excluded_count': int(campaign.excluded_count or 0),
        'excluded_no_consent': int(campaign.excluded_no_consent or 0),
        'excluded_invalid_phone': int(campaign.excluded_invalid_phone or 0),
        'excluded_not_found': int(campaign.excluded_not_found or 0),
        'queued_count': int(campaign.queued_count or 0),
        'processing_count': int(campaign.processing_count or 0),
        'accepted_count': int(campaign.accepted_count or 0),
        'sent_count': int(campaign.sent_count or 0),
        'delivered_count': int(campaign.delivered_count or 0),
        'read_count': int(campaign.read_count or 0),
        'failed_count': int(campaign.failed_count or 0),
        'unknown_count': int(campaign.unknown_count or 0),
        'duplicate_count': int(campaign.duplicate_count or 0),
        'status': campaign.status,
        'pause_code': campaign.pause_code or None,
        'pause_reason': campaign.pause_reason or None,
    }


def _validate_request_id(data):
    body_request_id = str(data.get('request_id', '')).strip()
    header_request_id = request.headers.get('Idempotency-Key', '').strip()
    if (
        body_request_id
        and header_request_id
        and body_request_id.lower() != header_request_id.lower()
    ):
        return None, ('request_id must match Idempotency-Key.', 400)
    value = header_request_id or body_request_id
    try:
        parsed = uuid.UUID(value, version=4)
        if str(parsed) != value.lower():
            raise ValueError
    except (ValueError, AttributeError):
        return None, ('request_id must be a canonical UUID v4.', 400)
    return str(parsed), None


def _log_direct_campaign(data, current_user, branch, filter_type, customers, requested_ids):
    """Record manual wa.me sends without invoking any server-side WhatsApp API."""
    sent_ids = data.get('sent_customer_ids') or []
    skipped_ids = data.get('skipped_customer_ids') or []
    if not isinstance(sent_ids, list) or not isinstance(skipped_ids, list):
        return jsonify({'error': 'Direct-send customer IDs must be arrays.'}), 400

    sent_set = {str(customer_id) for customer_id in sent_ids}
    skipped_set = {str(customer_id) for customer_id in skipped_ids}
    eligible = []
    excluded_no_consent = 0
    excluded_invalid_phone = 0
    for customer in customers:
        if customer.whatsapp_consent is not True:
            excluded_no_consent += 1
            continue
        if not normalize_indian_campaign_phone(customer.mobile):
            excluded_invalid_phone += 1
            continue
        eligible.append(customer)

    campaign = OfferCampaign(
        name=data.get('name', ''),
        message_text=data['message_text'],
        image_data=data.get('image_data'),
        image_mime_type=data.get('image_mime_type'),
        filter_type=filter_type,
        campaign_type=data.get('campaign_type', 'general'),
        branch=branch,
        requested_count=len(requested_ids),
        eligible_count=len(eligible),
        excluded_count=excluded_no_consent + excluded_invalid_phone,
        excluded_no_consent=excluded_no_consent,
        excluded_invalid_phone=excluded_invalid_phone,
        status='pending',
        created_by_id=str(current_user.get('user_id', '')) if current_user else '',
        created_by_name=current_user.get('name', 'Unknown') if current_user else 'Unknown',
    )
    campaign.save()

    sent_count = 0
    failed_count = 0
    now = datetime.utcnow()
    for customer in eligible:
        customer_id = str(customer.id)
        if customer_id in skipped_set or (sent_set and customer_id not in sent_set):
            failed_count += 1
            continue
        try:
            WhatsAppMessage(
                customer=customer,
                branch=branch or customer.branch,
                message_text=data['message_text'],
                delivery_status='sent',
                sent_at=now,
            ).save()
            sent_count += 1
        except Exception:
            failed_count += 1

    campaign.update(
        set__sent_count=sent_count,
        set__failed_count=failed_count,
        set__status='in_progress' if sent_count else 'failed',
        set__updated_at=datetime.utcnow(),
    )
    campaign.reload()
    return jsonify(_campaign_summary(campaign)), 200


def _classify_campaign_customers(customers, requested_ids):
    by_id = {str(customer.id): customer for customer in customers}
    excluded_not_found = sum(1 for customer_id in requested_ids if customer_id not in by_id)
    excluded_no_consent = 0
    excluded_invalid_phone = 0
    eligible = []
    for customer_id in requested_ids:
        customer = by_id.get(customer_id)
        if not customer:
            continue
        if customer.whatsapp_consent is not True:
            excluded_no_consent += 1
            continue
        normalized_phone = normalize_indian_campaign_phone(customer.mobile)
        if not normalized_phone:
            excluded_invalid_phone += 1
            continue
        eligible.append((customer, normalized_phone))
    return eligible, {
        'excluded_not_found': excluded_not_found,
        'excluded_no_consent': excluded_no_consent,
        'excluded_invalid_phone': excluded_invalid_phone,
    }


def _safe_campaign_error(error, service=None):
    return sanitize_meta_error_text(
        str(error),
        getattr(service, 'access_token', '') if service else '',
    )


def _load_or_create_campaign(
    *, data, current_user, branch, filter_type, request_id, request_hash,
    media_asset, requested_count, eligible_count, exclusions,
):
    existing = OfferCampaign.objects(client_request_id=request_id).first()
    if existing:
        if existing.request_hash != request_hash:
            return None, False, ('This request ID belongs to a different campaign.', 409)
        return existing, False, None

    excluded_count = sum(exclusions.values())
    campaign = OfferCampaign(
        name=data.get('name', ''),
        message_text=data['message_text'],
        filter_type=filter_type,
        campaign_type=data.get('campaign_type', 'general'),
        branch=branch,
        client_request_id=request_id,
        request_hash=request_hash,
        template_name=CAMPAIGN_TEMPLATE_NAME,
        language_code=CAMPAIGN_TEMPLATE_LANGUAGE,
        media_asset=media_asset,
        requested_count=requested_count,
        eligible_count=eligible_count,
        excluded_count=excluded_count,
        excluded_no_consent=exclusions['excluded_no_consent'],
        excluded_invalid_phone=exclusions['excluded_invalid_phone'],
        excluded_not_found=exclusions['excluded_not_found'],
        status='pending',
        created_by_id=str(current_user.get('user_id', '')) if current_user else '',
        created_by_name=current_user.get('name', 'Unknown') if current_user else 'Unknown',
    )
    try:
        campaign.save(force_insert=True)
        return campaign, True, None
    except NotUniqueError:
        existing = OfferCampaign.objects(client_request_id=request_id).first()
        if not existing or existing.request_hash != request_hash:
            return None, False, ('This request ID belongs to a different campaign.', 409)
        return existing, False, None


def _send_meta_campaign(data, current_user, branch, filter_type, customers, requested_ids):
    try:
        if get_app_runtime() != 'production' or is_demo_branch(branch):
            return jsonify({
                'error': 'Production campaigns are unavailable in this runtime.',
                'error_code': 'production_runtime_required',
            }), 403
    except RuntimeConfigurationError:
        return jsonify({
            'error': 'Application runtime is not configured.',
            'error_code': 'runtime_invalid',
        }), 503

    if not campaign_flag_enabled('WHATSAPP_PRODUCTION_SEND_ENABLED'):
        return jsonify({'error': 'Production sending is disabled.', 'error_code': 'send_disabled'}), 403
    if not campaign_flag_enabled('WHATSAPP_CAMPAIGN_SEND_ENABLED'):
        return jsonify({'error': 'Campaign sending is disabled.', 'error_code': 'campaign_disabled'}), 403

    request_id, request_error = _validate_request_id(data)
    if request_error:
        return jsonify({'error': request_error[0], 'error_code': 'invalid_request_id'}), request_error[1]

    template_name = data.get('template_name', CAMPAIGN_TEMPLATE_NAME)
    language_code = data.get('language', CAMPAIGN_TEMPLATE_LANGUAGE)
    media_asset_id = data.get('media_asset_id')
    if template_name != CAMPAIGN_TEMPLATE_NAME or language_code != CAMPAIGN_TEMPLATE_LANGUAGE:
        return jsonify({
            'error': 'Only the approved Priyanka promotional template is supported.',
            'error_code': 'campaign_template_not_allowed',
        }), 422
    if not isinstance(media_asset_id, str) or not ObjectId.is_valid(media_asset_id):
        return jsonify({
            'error': 'A valid private promotional image is required.',
            'error_code': 'campaign_media_required',
        }), 422

    eligible, exclusions = _classify_campaign_customers(customers, requested_ids)

    try:
        service = MetaWhatsAppService(production=True)
        service.assert_configured()
        sender = service.get_sender()
        if sender.get('phone_status') != 'CONNECTED':
            raise MetaWhatsAppError(
                'The production WhatsApp sender is not connected.',
                http_status=503,
                code='sender_not_connected',
            )
        template = next((
            item for item in service.get_templates(status='APPROVED')
            if item.get('name') == CAMPAIGN_TEMPLATE_NAME
            and item.get('language') == CAMPAIGN_TEMPLATE_LANGUAGE
            and item.get('status') == 'APPROVED'
            and item.get('category') == 'MARKETING'
        ), None)
        if not template:
            raise MetaWhatsAppError(
                'The Priyanka promotional template is not approved.',
                http_status=422,
                code='campaign_template_unavailable',
            )
        _production_template_image(template, media_asset_id)
        tenant_id, media_branch, _owner_id = _media_scope(current_user)
        media_asset = _find_scoped_media_asset(media_asset_id, tenant_id, media_branch)
        if not media_asset:
            raise MetaWhatsAppError(
                'The private promotional image is unavailable.',
                http_status=404,
                code='campaign_media_unavailable',
            )
    except (MetaWhatsAppError, R2MediaError) as exc:
        return jsonify({
            'error': _safe_campaign_error(exc, locals().get('service')),
            'error_code': getattr(exc, 'code', None) or 'campaign_validation_failed',
        }), getattr(exc, 'http_status', 503)

    branch_id = str(branch.id) if branch else ''
    request_hash = build_campaign_request_hash(
        customer_ids=requested_ids,
        media_asset_id=media_asset_id,
        branch_id=branch_id,
        message_text=data['message_text'],
    )
    campaign, created, conflict = _load_or_create_campaign(
        data=data,
        current_user=current_user,
        branch=branch,
        filter_type=filter_type,
        request_id=request_id,
        request_hash=request_hash,
        media_asset=media_asset,
        requested_count=len(requested_ids),
        eligible_count=len(eligible),
        exclusions=exclusions,
    )
    if conflict:
        return jsonify({'error': conflict[0], 'error_code': 'idempotency_conflict'}), conflict[1]

    account = {
        'waba_id': service.business_account_id,
        'phone_number_id': service.phone_number_id,
    }
    reservation = reserve_campaign_recipients(
        campaign, eligible, media_asset, account
    )
    duplicate_count = max(
        int(getattr(campaign, 'duplicate_count', 0) or 0),
        reservation['duplicate_count'],
    )
    campaign.update(set__duplicate_count=duplicate_count)
    campaign.duplicate_count = duplicate_count
    refresh_campaign_aggregates(campaign)
    if not created:
        return jsonify(_campaign_summary(campaign, duplicate=True)), 200

    try:
        first_batch = _process_campaign_batch(str(campaign.id))
    except Exception:
        first_batch = {
            'processed': False,
            'batch_size': campaign_batch_size(),
            'claimed_count': 0,
            'error_code': 'campaign_batch_start_failed',
        }
        refresh_campaign_aggregates(campaign)

    summary = first_batch.get('campaign') or _campaign_summary(campaign)
    summary['duplicate'] = False
    summary['first_batch'] = {
        key: first_batch[key]
        for key in (
            'processed', 'batch_size', 'claimed_count', 'accepted_in_batch',
            'failed_in_batch', 'unknown_in_batch', 'paused', 'deferred', 'error_code',
        )
        if key in first_batch
    }
    return jsonify(summary), 202


def _campaign_worker_authorized():
    expected = os.environ.get('WHATSAPP_CAMPAIGN_WORKER_SECRET', '')
    authorization = request.headers.get('Authorization', '')
    if not expected or expected != expected.strip() or len(expected) < 32:
        return False
    return hmac.compare_digest(
        authorization.encode('utf-8'),
        f'Bearer {expected}'.encode('utf-8'),
    )


def _crm_user_can_process_campaign(campaign_id, current_user):
    branch = get_selected_branch(request, current_user)
    if is_demo_branch(branch):
        return False
    campaign = apply_branch_scope(
        OfferCampaign.objects(id=campaign_id), branch, current_user
    ).first()
    return campaign is not None


def _campaign_worker_runtime_error():
    try:
        if get_app_runtime() != 'production':
            return jsonify({
                'error': 'Campaign processing is unavailable in this runtime.',
                'error_code': 'production_runtime_required',
            }), 403
    except RuntimeConfigurationError:
        return jsonify({
            'error': 'Application runtime is not configured.',
            'error_code': 'runtime_invalid',
        }), 503
    if not campaign_flag_enabled('WHATSAPP_PRODUCTION_SEND_ENABLED'):
        return jsonify({'error': 'Production sending is disabled.', 'error_code': 'send_disabled'}), 403
    if not campaign_flag_enabled('WHATSAPP_CAMPAIGN_SEND_ENABLED'):
        return jsonify({'error': 'Campaign sending is disabled.', 'error_code': 'campaign_disabled'}), 403
    return None


def _pause_worker_campaign(campaign, error, service=None, *, code=None):
    safe_error = _safe_campaign_error(error, service)
    pause_campaign(
        campaign,
        code or getattr(error, 'code', None) or 'campaign_processing_paused',
        safe_error or 'Campaign processing paused.',
    )
    refresh_campaign_aggregates(campaign)


def _process_campaign_batch(campaign_id=None):
    worker_id = str(uuid.uuid4())
    campaign = claim_campaign(worker_id, campaign_id)
    if not campaign:
        return {
            'processed': False,
            'batch_size': campaign_batch_size(),
            'claimed_count': 0,
        }

    expire_ambiguous_recipient_claims(campaign)
    refresh_campaign_aggregates(campaign)
    service = None
    try:
        service = MetaWhatsAppService(production=True)
        service.assert_configured()
        sender = service.get_sender()
        if sender.get('phone_status') != 'CONNECTED':
            raise MetaWhatsAppError(
                'The production WhatsApp sender is not connected.',
                http_status=503,
                code='sender_not_connected',
            )
        template = next((
            item for item in service.get_templates(status='APPROVED')
            if item.get('name') == CAMPAIGN_TEMPLATE_NAME
            and item.get('language') == CAMPAIGN_TEMPLATE_LANGUAGE
            and item.get('status') == 'APPROVED'
            and item.get('category') == 'MARKETING'
        ), None)
        if not template:
            raise MetaWhatsAppError(
                'The Priyanka promotional template is not approved.',
                http_status=422,
                code='campaign_template_unavailable',
            )
        media_asset_id = str(campaign.media_asset.id) if campaign.media_asset else ''
        _production_template_image(template, media_asset_id)
        media_asset = _find_scoped_media_asset(
            media_asset_id,
            f'production:{SALON_PRODUCTION_WABA_ID}',
            None,
        )
        if not media_asset:
            raise MetaWhatsAppError(
                'The private promotional image is unavailable.',
                http_status=404,
                code='campaign_media_unavailable',
            )
        media_id = campaign.meta_media_id or service.upload_image(
            _read_stored_image(media_asset), media_asset.content_type
        )
        if not campaign.meta_media_id:
            campaign.update(
                set__meta_media_id=media_id,
                set__media_uploaded_at=datetime.utcnow(),
                set__updated_at=datetime.utcnow(),
            )
            campaign.meta_media_id = media_id
    except (MetaWhatsAppError, R2MediaError) as exc:
        _pause_worker_campaign(campaign, exc, service)
        return {
            'processed': True,
            'campaign': _campaign_summary(campaign),
            'claimed_count': 0,
            'paused': True,
        }
    except Exception:
        error = MetaWhatsAppError(
            'Campaign preparation stopped unexpectedly.',
            code='campaign_preparation_error',
        )
        _pause_worker_campaign(campaign, error, service)
        return {
            'processed': True,
            'campaign': _campaign_summary(campaign),
            'claimed_count': 0,
            'paused': True,
        }

    account = {
        'waba_id': service.business_account_id,
        'phone_number_id': service.phone_number_id,
    }
    claimed_count = 0
    accepted_count = 0
    failed_count = 0
    unknown_count = 0
    paused = False
    deferred = False
    for _index in range(campaign_batch_size()):
        recipient = claim_queued_recipient(campaign, worker_id)
        if not recipient:
            break
        claimed_count += 1
        try:
            _enforce_send_rate_limits(
                campaign.created_by_id or 'campaign-worker',
                production=True,
            )
            result = service.send_template(
                recipient.normalized_recipient,
                CAMPAIGN_TEMPLATE_NAME,
                CAMPAIGN_TEMPLATE_LANGUAGE,
                media_id=media_id,
            )
            set_recipient_status(
                recipient,
                'accepted',
                message_id=result['message_id'],
            )
            accepted_count += 1
            for event in WhatsAppWebhookEvent.objects(
                meta_message_id=result['message_id'],
                event_type='status',
                **account,
            ).order_by('created_at'):
                update_campaign_recipient_status(
                    result['message_id'], event.status, account=account
                )
        except MetaWhatsAppError as exc:
            safe_error = _safe_campaign_error(exc, service)
            if exc.code == 'rate_limited':
                set_recipient_status(
                    recipient,
                    'queued',
                    error_code='rate_limited',
                    error_message=safe_error,
                )
                deferred = True
                break
            if campaign_error_requires_pause(exc):
                uncertain = exc.code in {
                    'network_error', 'missing_message_id', 'invalid_response'
                }
                set_recipient_status(
                    recipient,
                    'unknown' if uncertain else 'queued',
                    error_code=exc.code or 'campaign_processing_paused',
                    error_message=safe_error,
                )
                unknown_count += int(uncertain)
                _pause_worker_campaign(campaign, exc, service)
                paused = True
                break
            set_recipient_status(
                recipient,
                'failed',
                error_code=exc.code or 'meta_error',
                error_message=safe_error,
            )
            failed_count += 1
        except Exception as exc:
            set_recipient_status(
                recipient,
                'unknown',
                error_code='campaign_worker_error',
                error_message='Campaign processing stopped with an unknown delivery outcome.',
            )
            unknown_count += 1
            _pause_worker_campaign(
                campaign,
                MetaWhatsAppError(
                    'Campaign processing stopped unexpectedly.',
                    code='campaign_worker_error',
                ),
                service,
            )
            paused = True
            break

    refresh_campaign_aggregates(campaign)
    if not paused:
        release_campaign_lease(campaign)
    return {
        'processed': True,
        'campaign': _campaign_summary(campaign),
        'batch_size': campaign_batch_size(),
        'claimed_count': claimed_count,
        'accepted_in_batch': accepted_count,
        'failed_in_batch': failed_count,
        'unknown_in_batch': unknown_count,
        'paused': paused,
        'deferred': deferred,
    }


@campaign_bp.route('/process-queue', methods=['POST'])
def process_campaign_queue():
    """Process one durable batch for a trusted worker or authenticated CRM user."""
    trusted_worker = _campaign_worker_authorized()
    current_user = None if trusted_worker else get_current_user()
    if not trusted_worker and not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    if not trusted_worker and current_user.get('role') not in ('manager', 'owner'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json(silent=True) or {}
    campaign_id = data.get('campaign_id')
    if campaign_id is not None and (
        not isinstance(campaign_id, str) or not ObjectId.is_valid(campaign_id)
    ):
        return jsonify({'error': 'campaign_id is invalid.'}), 400
    if not trusted_worker and campaign_id is None:
        return jsonify({'error': 'campaign_id is required.'}), 400

    runtime_error = _campaign_worker_runtime_error()
    if runtime_error:
        return runtime_error
    if not trusted_worker and not _crm_user_can_process_campaign(
        campaign_id, current_user
    ):
        return jsonify({'error': 'Campaign not found.'}), 404
    return jsonify(_process_campaign_batch(campaign_id)), 200


@campaign_bp.route('/<campaign_id>/resume', methods=['POST'])
@require_role('manager', 'owner')
def resume_paused_campaign(campaign_id, current_user=None):
    runtime_error = _campaign_worker_runtime_error()
    if runtime_error:
        return runtime_error
    if not ObjectId.is_valid(campaign_id):
        return jsonify({'error': 'Campaign not found.'}), 404
    branch = get_selected_branch(request, current_user)
    query = apply_branch_scope(
        OfferCampaign.objects(id=campaign_id), branch, current_user
    )
    campaign = query.first()
    if not campaign:
        return jsonify({'error': 'Campaign not found.'}), 404
    if campaign.status != 'paused' or not campaign.queued_count:
        return jsonify({'error': 'Campaign is not paused with queued recipients.'}), 409
    resume_campaign(campaign)
    refresh_campaign_aggregates(campaign)
    return jsonify(_campaign_summary(campaign)), 200


@campaign_bp.route('/<campaign_id>', methods=['GET'])
@require_role('manager', 'owner')
def get_campaign_progress(campaign_id, current_user=None):
    if not ObjectId.is_valid(campaign_id):
        return jsonify({'error': 'Campaign not found.'}), 404
    branch = get_selected_branch(request, current_user)
    campaign = apply_branch_scope(
        OfferCampaign.objects(id=campaign_id), branch, current_user
    ).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found.'}), 404
    refresh_campaign_aggregates(campaign)
    return jsonify({
        **_campaign_summary(campaign),
        'name': campaign.name or 'Untitled Campaign',
        'template_name': campaign.template_name,
        'language': campaign.language_code,
        'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
        'updated_at': campaign.updated_at.isoformat() if campaign.updated_at else None,
    }), 200

@campaign_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_campaigns(current_user=None):
    """Get campaign history"""
    try:
        branch = get_selected_branch(request, current_user)
        campaign_type = request.args.get('type')  # Optional filter: 'general' or 'birthday'
        
        query = OfferCampaign.objects()
        query = apply_branch_scope(query, branch, current_user)
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
                'template_name': getattr(campaign, 'template_name', None),
                'language': getattr(campaign, 'language_code', None),
                'requested_count': getattr(campaign, 'requested_count', 0) or 0,
                'eligible_count': getattr(campaign, 'eligible_count', 0) or 0,
                'excluded_count': getattr(campaign, 'excluded_count', 0) or 0,
                'excluded_no_consent': getattr(campaign, 'excluded_no_consent', 0) or 0,
                'excluded_invalid_phone': getattr(campaign, 'excluded_invalid_phone', 0) or 0,
                'queued_count': getattr(campaign, 'queued_count', 0) or 0,
                'processing_count': getattr(campaign, 'processing_count', 0) or 0,
                'accepted_count': getattr(campaign, 'accepted_count', 0) or 0,
                'sent_count': campaign.sent_count,
                'delivered_count': getattr(campaign, 'delivered_count', 0) or 0,
                'read_count': getattr(campaign, 'read_count', 0) or 0,
                'failed_count': campaign.failed_count,
                'unknown_count': getattr(campaign, 'unknown_count', 0) or 0,
                'duplicate_count': getattr(campaign, 'duplicate_count', 0) or 0,
                'status': campaign.status,
                'pause_code': getattr(campaign, 'pause_code', None),
                'pause_reason': getattr(campaign, 'pause_reason', None),
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

