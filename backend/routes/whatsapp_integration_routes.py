"""Meta WhatsApp Cloud API endpoints for demo and Priyanka."""
import hashlib
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timedelta

from bson import ObjectId
from flask import Blueprint, Response, current_app, jsonify, request
from mongoengine.errors import NotUniqueError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from models import (
    Customer,
    WhatsAppMediaAsset,
    WhatsAppRateLimit,
    WhatsAppTestMessage,
    WhatsAppWebhookEvent,
)
from services.r2_media_service import (
    R2MediaConfigurationError,
    R2MediaError,
    R2MediaService,
    missing_r2_configuration,
)
from utils.env_config import RuntimeConfigurationError, get_app_runtime
from utils.whatsapp_auth import require_whatsapp_owner
from utils.branch_filter import get_demo_branch
from utils.image_validation import (
    MAX_IMAGE_BYTES,
    ImageValidationError,
    build_media_object_key,
    normalize_uploaded_image,
)
from utils.meta_whatsapp_service import (
    MetaWhatsAppError,
    MetaWhatsAppService,
    SALON_PRODUCTION_WABA_ID,
    TestRecipient,
    extract_webhook_events,
    load_test_recipients,
    verify_webhook_signature,
)


whatsapp_integration_bp = Blueprint('whatsapp_integration', __name__)
ALLOWED_TEMPLATE = 'hello_world'
MAX_WEBHOOK_BYTES = 1024 * 1024
STATUS_ORDER = ['pending', 'accepted', 'sent', 'delivered', 'read']
WEBHOOK_SIGNATURE_RE = re.compile(r'^sha256=[0-9a-fA-F]{64}$')
MAX_MEDIA_MULTIPART_BYTES = MAX_IMAGE_BYTES + (512 * 1024)
MAX_MEDIA_LIST_ITEMS = 50


def _production_request():
    return get_app_runtime() == 'production'


@whatsapp_integration_bp.errorhandler(RuntimeConfigurationError)
def handle_runtime_configuration_error(_error):
    return jsonify({
        'error': 'Application runtime is not configured.',
        'error_code': 'runtime_invalid',
    }), 503


def _enabled(name):
    return os.environ.get(name, '').strip().lower() == 'true'


def _bounded_log_header(value):
    return ''.join(
        character if character.isascii() and character.isprintable() else '?'
        for character in str(value or '')
    )[:160]


def _log_webhook_signature_rejected(raw_body, signature_header, app_secret):
    signature_match = WEBHOOK_SIGNATURE_RE.fullmatch(signature_header or '')
    app_secret_bytes = app_secret.encode('utf-8')
    record = {
        'event': 'whatsapp_webhook_signature_rejected',
        'signature_header_present': bool(signature_header),
        'signature_header_format_valid': bool(signature_match),
        'raw_body_byte_length': len(raw_body),
        'app_secret_length': len(app_secret),
        'app_secret_sha256_prefix': hashlib.sha256(
            app_secret_bytes
        ).hexdigest()[:12],
        'raw_body_sha256_prefix': hashlib.sha256(raw_body).hexdigest()[:12],
        'supplied_signature_prefix': (
            signature_header.split('=', 1)[1][:12].lower()
            if signature_match else None
        ),
        'calculated_signature_prefix': hmac.new(
            app_secret_bytes,
            raw_body,
            hashlib.sha256,
        ).hexdigest()[:12],
        'Content-Type': _bounded_log_header(request.headers.get('Content-Type')),
        'app_secret_configured': bool(app_secret),
        'APP_RUNTIME': _bounded_log_header(os.environ.get('APP_RUNTIME')),
        'VERCEL_ENV': _bounded_log_header(os.environ.get('VERCEL_ENV')),
    }
    content_encoding = request.headers.get('Content-Encoding')
    if content_encoding:
        record['Content-Encoding'] = _bounded_log_header(content_encoding)
    current_app.logger.warning(
        '%s',
        json.dumps(record, ensure_ascii=True, separators=(',', ':'), sort_keys=True),
    )


def _production_state(service, *, inspect_subscription=False):
    sender = service.get_sender()
    business_name = service.get_business()
    try:
        templates = service.get_templates(status='APPROVED', first_page=True)
    except MetaWhatsAppError:
        templates = None
    billing_required = not _enabled('WHATSAPP_PRODUCTION_BILLING_VERIFIED')
    webhook_verified = _enabled('WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED')
    subscription_present = None
    if inspect_subscription or webhook_verified:
        try:
            subscription_present = service.has_webhook_subscriptions()
        except MetaWhatsAppError:
            pass
    webhook_ready = webhook_verified and subscription_present is True

    base_reason = None
    if billing_required:
        base_reason = 'Add and verify a valid payment method in Meta WhatsApp Manager.'
    elif sender['phone_status'] != 'CONNECTED':
        base_reason = 'Verify that the production phone is connected in WhatsApp Manager.'
    elif templates is None:
        base_reason = 'Verify template access in Meta WhatsApp Manager.'
    has_approved_template = any(
        item['name'] and item['name'] != ALLOWED_TEMPLATE for item in (templates or [])
    )
    if not base_reason and not has_approved_template:
        base_reason = 'Verify an approved Priyanka template.'

    recipient_ready = False
    recipient_error = None
    try:
        recipient_ready = bool(load_test_recipients(production=True))
    except RuntimeError:
        recipient_error = 'The controlled test recipient allowlist is invalid.'

    controlled_test_reason = base_reason
    if not controlled_test_reason and not recipient_ready:
        controlled_test_reason = (
            recipient_error or 'Add an explicitly opted-in controlled test recipient.'
        )
    if not controlled_test_reason and not _enabled('WHATSAPP_PRODUCTION_TEST_ENABLED'):
        controlled_test_reason = 'Controlled production testing is disabled.'
    controlled_test_enabled = controlled_test_reason is None

    send_disabled_reason = base_reason
    if not send_disabled_reason and not webhook_ready:
        send_disabled_reason = 'Validate production delivery, read and inbound webhooks.'
    if not send_disabled_reason and not _enabled('WHATSAPP_PRODUCTION_SEND_ENABLED'):
        send_disabled_reason = 'Production customer sends are awaiting final approval.'
    customer_sending_enabled = (
        send_disabled_reason is None
    )
    return {
        'connected': True,
        'sender': sender,
        'business_name': business_name or sender['verified_name'],
        'waba_id': service.business_account_id,
        'phone_number_id': service.phone_number_id,
        'display_phone_number': sender['display_phone_number'],
        'verified_name': sender['verified_name'],
        'template_access': templates is not None,
        'billing_required': billing_required,
        'webhook_ready': webhook_ready,
        'waba_has_webhook_subscriptions': subscription_present,
        'send_enabled': customer_sending_enabled,
        'sending_enabled': customer_sending_enabled,
        'controlled_test_enabled': controlled_test_enabled,
        'controlled_test_recipient_ready': recipient_ready,
        'controlled_test_disabled_reason': controlled_test_reason,
        'send_disabled_reason': send_disabled_reason,
    }


def _safe_limit(name, default, maximum):
    try:
        return max(1, min(int(os.environ.get(name, default)), maximum))
    except (TypeError, ValueError):
        return default


def _message_dict(message):
    return {
        'request_id': message.client_request_id,
        'recipient_label': message.recipient_label,
        'recipient_last4': message.recipient_last4,
        'template_name': message.template_name,
        'language': message.language_code,
        'message_id': message.meta_message_id or None,
        'status': message.status,
        'error_code': message.error_code or None,
        'error_subcode': getattr(message, 'error_subcode', None) or None,
        'error_message': message.error_message or None,
        'error_details': getattr(message, 'error_details', None) or None,
        'meta_http_status': getattr(message, 'meta_http_status', None),
        'fbtrace_id': getattr(message, 'fbtrace_id', None) or None,
        'created_at': message.created_at.isoformat() + 'Z' if message.created_at else None,
        'updated_at': message.updated_at.isoformat() + 'Z' if message.updated_at else None,
    }


def _media_scope(current_user):
    if _production_request():
        return f'production:{SALON_PRODUCTION_WABA_ID}', None, str(current_user['user_id'])
    branch = get_demo_branch()
    if not branch:
        raise R2MediaConfigurationError('The isolated demo branch is unavailable.')
    branch_id = str(branch.id)
    return f'demo:{branch_id}', branch, str(current_user['user_id'])


def _media_asset_dict(asset):
    return {
        'id': str(asset.id),
        'display_filename': asset.display_filename,
        'content_type': asset.content_type,
        'byte_size': asset.byte_size,
        'width': asset.width,
        'height': asset.height,
        'status': asset.status,
        'created_at': asset.created_at.isoformat() + 'Z' if asset.created_at else None,
        'preview_url': f'/api/integrations/whatsapp/media/{asset.id}/content',
    }


def _find_scoped_media_asset(asset_id, tenant_id, branch):
    if not ObjectId.is_valid(asset_id):
        return None
    return WhatsAppMediaAsset.objects(
        id=asset_id,
        tenant_id=tenant_id,
        branch=branch,
        status='ready',
    ).first()


def _read_stored_image(asset):
    stored = R2MediaService(production=_production_request()).get_image(
        asset.object_key, max_bytes=MAX_IMAGE_BYTES,
    )
    if (
        len(stored.data) != asset.byte_size
        or hashlib.sha256(stored.data).hexdigest() != asset.sha256
    ):
        raise MetaWhatsAppError('The stored image failed its integrity check.', http_status=502)
    return stored.data


def _find_recipient(recipient_id):
    for recipient in load_test_recipients():
        if recipient.recipient_id == recipient_id:
            return recipient
    return None


def _reserve_message(request_id, recipient, language_code, owner_id, *,
                     template_name=ALLOWED_TEMPLATE, production_fields=None):
    now = datetime.utcnow()
    document = {
        'client_request_id': request_id,
        'recipient_id': recipient.recipient_id,
        'recipient_label': recipient.label,
        'recipient_last4': recipient.phone[-4:],
        'template_name': template_name,
        'language_code': language_code,
        'status': 'pending',
        'sent_by_owner_id': owner_id,
        'created_at': now,
        'updated_at': now,
        'status_updated_at': now,
        **(production_fields or {}),
    }
    collection = WhatsAppTestMessage._get_collection()
    try:
        previous = collection.find_one_and_update(
            {'client_request_id': request_id},
            {'$setOnInsert': document},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        created = previous is None
    except DuplicateKeyError:
        created = False
    return WhatsAppTestMessage.objects(client_request_id=request_id).first(), created


def _consume_counter(bucket_key, expires_at):
    collection = WhatsAppRateLimit._get_collection()
    update = {
        '$inc': {'count': 1},
        '$setOnInsert': {
            'expires_at': expires_at,
            'created_at': datetime.utcnow(),
        },
    }
    try:
        result = collection.find_one_and_update(
            {'bucket_key': bucket_key},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        # Two serverless instances can race to create the same new bucket. The
        # loser retries as an update, preserving one shared atomic counter.
        result = collection.find_one_and_update(
            {'bucket_key': bucket_key},
            {'$inc': {'count': 1}},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise MetaWhatsAppError(
                'WhatsApp rate limiter is temporarily unavailable.',
                http_status=503,
                code='rate_limiter_unavailable',
            )
    return int(result.get('count', 0))


def _enforce_send_rate_limits(owner_id, *, production=False):
    now = datetime.utcnow()
    minute_start = now.replace(second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    buckets = [
        (
            f'owner:{owner_id}:minute:{minute_start:%Y%m%d%H%M}',
            minute_start + timedelta(minutes=1),
            _safe_limit('META_WA_RATE_LIMIT_PER_MINUTE', 3, 30),
        ),
        (
            f'owner:{owner_id}:day:{day_start:%Y%m%d}',
            day_start + timedelta(days=1),
            _safe_limit('META_WA_RATE_LIMIT_PER_DAY', 20, 100),
        ),
        (
            f'global:day:{day_start:%Y%m%d}',
            day_start + timedelta(days=1),
            _safe_limit('META_WA_GLOBAL_RATE_LIMIT_PER_DAY', 50, 200),
        ),
    ]
    for bucket_key, expires_at, limit in buckets:
        if production:
            bucket_key = f'production:{bucket_key}'
        if _consume_counter(bucket_key, expires_at) > limit:
            raise MetaWhatsAppError(
                'WhatsApp send limit reached. Try again after the rate-limit window resets.',
                http_status=429,
                code='rate_limited',
            )


def _update_message_status(message_id, new_status, error_code='', error_message='', *,
                           account=None):
    if new_status not in STATUS_ORDER and new_status != 'failed':
        return

    if new_status == 'failed':
        allowed_current = ['pending', 'accepted', 'sent', 'unknown']
    else:
        new_rank = STATUS_ORDER.index(new_status)
        allowed_current = STATUS_ORDER[:new_rank]
        if new_status == 'pending':
            allowed_current = []
        allowed_current.append('unknown')

    if not allowed_current:
        return
    update = {
        'status': new_status,
        'updated_at': datetime.utcnow(),
        'status_updated_at': datetime.utcnow(),
    }
    if error_code:
        update['error_code'] = error_code[:100]
    if error_message:
        update['error_message'] = error_message[:500]
    WhatsAppTestMessage._get_collection().update_one(
        {
            'meta_message_id': message_id,
            'status': {'$in': allowed_current},
            **(account or {}),
        },
        {'$set': update},
    )


@whatsapp_integration_bp.get('/health')
def demo_health():
    return jsonify({'error': 'Not found'}), 404


@whatsapp_integration_bp.get('/status')
@require_whatsapp_owner
def get_status(current_user):
    if _production_request():
        service = MetaWhatsAppService(production=True)
        response = {
            'runtime': 'production',
            'environment': 'production',
            'connected': False,
            'send_enabled': False,
            'sending_enabled': False,
            'controlled_test_enabled': False,
            'bulk_campaigns_enabled': False,
            'billing_required': not _enabled('WHATSAPP_PRODUCTION_BILLING_VERIFIED'),
            'webhook_configured': not any(
                name in service.missing_configuration() for name in MetaWhatsAppService.WEBHOOK_ENV
            ),
            'webhook_ready': False,
            'waba_has_webhook_subscriptions': None,
            'template_access': False,
            'media_configured': not missing_r2_configuration(),
            'missing_configuration': service.missing_configuration(),
        }
        try:
            response.update(_production_state(service, inspect_subscription=True))
        except MetaWhatsAppError as exc:
            response.update(error_code=exc.code, send_disabled_reason=str(exc))
        return jsonify(response)

    service = MetaWhatsAppService()
    missing = service.missing_configuration()
    webhook_missing = [
        name for name in ('META_WA_APP_SECRET', 'META_WA_WEBHOOK_VERIFY_TOKEN')
        if not os.environ.get(name, '').strip()
    ]
    response = {
        'runtime': 'demo',
        'connected': False,
        'send_enabled': not missing,
        'sending_enabled': not missing,
        'controlled_test_enabled': not missing,
        'bulk_campaigns_enabled': False,
        'webhook_configured': not webhook_missing,
        'webhook_ready': not webhook_missing,
        'media_configured': not missing_r2_configuration(),
        'missing_configuration': missing + webhook_missing,
        'allowed_template': ALLOWED_TEMPLATE,
    }
    if missing:
        return jsonify(response)
    try:
        response['sender'] = service.get_sender()
        response['connected'] = True
    except MetaWhatsAppError as exc:
        response['error'] = str(exc)
        response['error_code'] = exc.code
    return jsonify(response)


@whatsapp_integration_bp.get('/recipients')
@require_whatsapp_owner
def get_recipients(current_user):
    try:
        recipients = [
            item.public_dict()
            for item in load_test_recipients(production=_production_request())
        ]
    except RuntimeError as exc:
        return jsonify({'error': str(exc), 'recipients': []}), 503
    return jsonify({'recipients': recipients})


@whatsapp_integration_bp.get('/templates')
@require_whatsapp_owner
def get_templates(current_user):
    production = _production_request()
    status = request.args.get('status', '').strip().upper()
    if status and not re.fullmatch(r'[A-Z_]{1,40}', status):
        return jsonify({'error': 'Invalid template status.', 'templates': []}), 400
    try:
        service = MetaWhatsAppService(production=production)
        templates = service.get_templates(status=status) if status else service.get_templates()
        return jsonify({
            'templates': templates,
            'allowed_template': None if production else ALLOWED_TEMPLATE,
            'source': 'meta_graph_api',
        })
    except MetaWhatsAppError as exc:
        return jsonify({'error': str(exc), 'error_code': exc.code, 'templates': []}), exc.http_status


@whatsapp_integration_bp.post('/media')
@require_whatsapp_owner
def upload_media(current_user):
    if request.content_length and request.content_length > MAX_MEDIA_MULTIPART_BYTES:
        return jsonify({'error': 'Image must be 3 MiB or smaller.'}), 413

    try:
        tenant_id, branch, owner_id = _media_scope(current_user)
        storage = R2MediaService(production=_production_request())
        image = normalize_uploaded_image(request.files.get('file'))
        object_key = build_media_object_key(image.extension, production=_production_request())
        stored = storage.put_image(object_key, image)
    except ImageValidationError as exc:
        return jsonify({'error': str(exc)}), exc.status_code
    except (R2MediaConfigurationError, R2MediaError) as exc:
        return jsonify({'error': str(exc)}), 503

    asset = WhatsAppMediaAsset(
        tenant_id=tenant_id,
        branch=branch,
        uploaded_by_owner_id=owner_id,
        object_key=object_key,
        display_filename=image.display_filename,
        content_type=image.content_type,
        byte_size=image.byte_size,
        width=image.width,
        height=image.height,
        sha256=image.sha256_hex,
        storage_etag=stored.etag,
        status='ready',
    )
    try:
        asset.save(force_insert=True)
    except Exception as exc:
        current_app.logger.error(
            'WhatsApp media metadata persistence failed: %s',
            type(exc).__name__,
        )
        try:
            storage.delete_image(object_key)
        except R2MediaError as cleanup_error:
            current_app.logger.error(
                'WhatsApp media orphan cleanup failed: %s',
                type(cleanup_error).__name__,
            )
        return jsonify({'error': 'Image metadata could not be saved.'}), 503

    return jsonify({'media': _media_asset_dict(asset)}), 201


@whatsapp_integration_bp.get('/media')
@require_whatsapp_owner
def list_media(current_user):
    try:
        tenant_id, branch, _owner_id = _media_scope(current_user)
    except R2MediaConfigurationError as exc:
        return jsonify({'error': str(exc), 'media': []}), 503

    try:
        assets = WhatsAppMediaAsset.objects(
            tenant_id=tenant_id,
            branch=branch,
            status='ready',
        ).order_by('-created_at').limit(MAX_MEDIA_LIST_ITEMS)
    except Exception as exc:
        current_app.logger.error(
            'WhatsApp media listing failed: %s',
            type(exc).__name__,
        )
        return jsonify({'error': 'Images could not be loaded.', 'media': []}), 503
    return jsonify({'media': [_media_asset_dict(asset) for asset in assets]})


@whatsapp_integration_bp.get('/media/<asset_id>/content')
@require_whatsapp_owner
def get_media_content(asset_id, current_user):
    try:
        tenant_id, branch, _owner_id = _media_scope(current_user)
    except R2MediaConfigurationError as exc:
        return jsonify({'error': str(exc)}), 503

    try:
        asset = _find_scoped_media_asset(asset_id, tenant_id, branch)
    except Exception as exc:
        current_app.logger.error(
            'WhatsApp media lookup failed: %s',
            type(exc).__name__,
        )
        return jsonify({'error': 'Image could not be loaded.'}), 503
    if not asset:
        return jsonify({'error': 'Image not found.'}), 404

    try:
        image_data = _read_stored_image(asset)
    except MetaWhatsAppError as exc:
        return jsonify({'error': str(exc)}), exc.http_status
    except (R2MediaConfigurationError, R2MediaError) as exc:
        return jsonify({'error': str(exc)}), 503

    response = Response(image_data, mimetype=asset.content_type)
    response.headers['Content-Disposition'] = (
        f'inline; filename="{asset.display_filename}"'
    )
    response.headers['Cache-Control'] = 'private, no-store, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


@whatsapp_integration_bp.get('/messages')
@require_whatsapp_owner
def list_messages(current_user):
    messages = WhatsAppTestMessage.objects
    if _production_request():
        messages = messages(waba_id=SALON_PRODUCTION_WABA_ID)
    messages = messages.order_by('-created_at').limit(50)
    return jsonify({'messages': [_message_dict(message) for message in messages]})


def _production_recipient(data, controlled_test):
    if controlled_test:
        return next((
            recipient for recipient in load_test_recipients(production=True)
            if recipient.recipient_id == data.get('recipient_id')
        ), None)

    customer_id = data.get('customer_id')
    if not isinstance(customer_id, str) or not ObjectId.is_valid(customer_id):
        return None
    customer = Customer.objects(id=customer_id, merged_into=None, whatsapp_consent=True).first()
    if not customer or (customer.branch and customer.branch == get_demo_branch()):
        return None
    mobile = re.sub(r'[ ().-]', '', customer.mobile)
    if re.fullmatch(r'[6-9][0-9]{9}', mobile):
        mobile = f'91{mobile}'
    if not re.fullmatch(r'\+?[1-9][0-9]{7,14}', mobile):
        return None
    return TestRecipient(str(customer.id), 'CRM customer', mobile.lstrip('+'))


def _production_template_image(template, media_asset_id):
    components = template.get('components')
    if not isinstance(components, list) or not components:
        raise MetaWhatsAppError('Template components are unavailable.', http_status=422)
    image_header = False
    for component in components:
        if not isinstance(component, dict):
            raise MetaWhatsAppError('Template components are invalid.', http_status=422)
        component_type = component.get('type')
        if '{{' in str(component.get('text', '')):
            raise MetaWhatsAppError('Template variables are not supported by this send path.', http_status=422)
        if component_type == 'HEADER' and component.get('format') == 'IMAGE':
            image_header = True
        elif component_type not in {'BODY', 'FOOTER'} and (
            component_type != 'HEADER' or component.get('format') != 'TEXT'
        ):
            raise MetaWhatsAppError('This template has unsupported components.', http_status=422)
    if bool(media_asset_id) != image_header:
        raise MetaWhatsAppError('Select a private image only for an image-header template.', http_status=422)


def _send_production_message(data, request_id, controlled_test, current_user):
    flag = 'WHATSAPP_PRODUCTION_TEST_ENABLED' if controlled_test else 'WHATSAPP_PRODUCTION_SEND_ENABLED'
    if not _enabled(flag):
        return jsonify({'error': 'Production sending is disabled.', 'error_code': 'send_disabled'}), 403

    template_name = data.get('template_name')
    language_code = data.get('language')
    media_asset_id = data.get('media_asset_id', '')
    if (
        not isinstance(template_name, str)
        or not re.fullmatch(r'[a-z0-9_]{1,100}', template_name)
        or template_name == ALLOWED_TEMPLATE
        or not isinstance(language_code, str)
        or not re.fullmatch(r'[a-z]{2,3}(?:_[A-Z]{2})?', language_code)
        or not isinstance(media_asset_id, str)
        or (media_asset_id and not ObjectId.is_valid(media_asset_id))
    ):
        return jsonify({'error': 'Select a Priyanka template, language and valid media asset.'}), 400

    service = MetaWhatsAppService(production=True)
    try:
        service.assert_configured()
        recipient = _production_recipient(data, controlled_test)
        if not recipient:
            return jsonify({'error': 'An eligible opted-in recipient is required.'}), 403
        readiness = _production_state(service)
        field = 'controlled_test_enabled' if controlled_test else 'sending_enabled'
        if not readiness[field]:
            reason = readiness['send_disabled_reason'] or 'Production testing is disabled.'
            return jsonify({'error': reason, 'error_code': 'send_disabled'}), 403
        template = next((
            item for item in service.get_templates(status='APPROVED')
            if item['name'] == template_name and item['language'] == language_code
        ), None)
        if not template:
            return jsonify({'error': 'The selected Priyanka template is not approved.'}), 422
        _production_template_image(template, media_asset_id)
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), getattr(exc, 'http_status', 503)

    owner_id = str(current_user['user_id'])
    account = {'waba_id': service.business_account_id, 'phone_number_id': service.phone_number_id}
    send_kind = 'controlled_test' if controlled_test else 'customer'
    message, created = _reserve_message(
        request_id, recipient, language_code, owner_id, template_name=template_name,
        production_fields={**account, 'send_kind': send_kind, 'media_asset_id': media_asset_id},
    )
    if not created:
        if (
            message.sent_by_owner_id != owner_id
            or message.waba_id != account['waba_id']
            or message.phone_number_id != account['phone_number_id']
            or message.recipient_id != recipient.recipient_id
            or message.template_name != template_name
            or message.language_code != language_code
            or message.send_kind != send_kind
            or (message.media_asset_id or '') != media_asset_id
        ):
            return jsonify({'error': 'This request ID belongs to a different send.'}), 409
        return jsonify({'duplicate': True, 'message': _message_dict(message)}), (
            202 if message.status == 'pending' else 200
        )

    try:
        _enforce_send_rate_limits(owner_id, production=True)
        media_id = None
        if media_asset_id:
            tenant_id, branch, _ = _media_scope(current_user)
            asset = _find_scoped_media_asset(media_asset_id, tenant_id, branch)
            if not asset:
                raise MetaWhatsAppError('Image not found.', http_status=404)
            media_id = service.upload_image(_read_stored_image(asset), asset.content_type)
        result = service.send_template(
            recipient.phone, template_name, language_code, media_id=media_id,
        )
    except (MetaWhatsAppError, R2MediaError) as exc:
        now = datetime.utcnow()
        code = getattr(exc, 'code', None)
        message.update(
            set__status='unknown' if code in {'network_error', 'missing_message_id', 'invalid_response'} else 'failed',
            set__error_code=code or 'send_error',
            set__error_message=str(exc)[:500],
            set__updated_at=now,
            set__status_updated_at=now,
        )
        return jsonify({'error': str(exc), 'error_code': code}), getattr(exc, 'http_status', 503)

    now = datetime.utcnow()
    message.update(
        set__meta_message_id=result['message_id'], set__status='accepted',
        set__updated_at=now, set__status_updated_at=now,
    )
    # Meta can deliver a callback before the send response is persisted.
    events = WhatsAppWebhookEvent.objects(
        meta_message_id=result['message_id'], event_type='status', **account,
    ).order_by('created_at')
    for event in events:
        _update_message_status(
            result['message_id'], event.status, account=account,
        )
    message.reload()
    return jsonify({'duplicate': False, 'message': _message_dict(message)}), 201


@whatsapp_integration_bp.post('/messages')
@whatsapp_integration_bp.post('/test-messages', defaults={'controlled_test': True})
@require_whatsapp_owner
def send_message(current_user, controlled_test=False):
    production = _production_request()
    if controlled_test and not production:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected a JSON object.'}), 400
    body_request_id = str(data.get('request_id', '')).strip()
    header_request_id = request.headers.get('Idempotency-Key', '').strip() if production else ''
    if body_request_id and header_request_id and body_request_id.lower() != header_request_id.lower():
        return jsonify({'error': 'request_id must match Idempotency-Key.'}), 400
    request_id = header_request_id or body_request_id
    recipient_id = str(data.get('recipient_id', '')).strip()
    template_name = str(data.get('template_name', '')).strip()
    language_code = str(data.get('language', 'en_US')).strip()

    try:
        parsed_request_id = uuid.UUID(request_id, version=4)
        if str(parsed_request_id) != request_id.lower():
            raise ValueError
    except (ValueError, AttributeError):
        return jsonify({'error': 'request_id must be a canonical UUID v4.'}), 400
    if not production and template_name != ALLOWED_TEMPLATE:
        return jsonify({'error': 'Only the allowlisted hello_world template can be sent.'}), 400
    if production:
        return _send_production_message(data, str(parsed_request_id), controlled_test, current_user)
    if not language_code or len(language_code) > 20:
        return jsonify({'error': 'A valid template language is required.'}), 400

    try:
        recipient = _find_recipient(recipient_id)
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 503
    if not recipient:
        return jsonify({'error': 'Recipient is not on the server-side test allowlist.'}), 403

    message, created = _reserve_message(
        request_id,
        recipient,
        language_code,
        str(current_user['user_id']),
    )
    if not created:
        status_code = 202 if message.status == 'pending' else 200
        return jsonify({'duplicate': True, 'message': _message_dict(message)}), status_code

    try:
        _enforce_send_rate_limits(str(current_user['user_id']))
        service = MetaWhatsAppService()
        templates = service.get_templates()
        template = next(
            (
                item for item in templates
                if item['name'] == ALLOWED_TEMPLATE
                and item['language'] == language_code
                and item['status'] == 'APPROVED'
            ),
            None,
        )
        if not template:
            raise MetaWhatsAppError(
                'The allowlisted hello_world template is not approved for the selected language.',
                http_status=422,
                code='template_unavailable',
            )
        result = service.send_template(recipient.phone, ALLOWED_TEMPLATE, language_code)
        now = datetime.utcnow()
        message.update(
            set__meta_message_id=result['message_id'],
            set__status='accepted',
            set__updated_at=now,
            set__status_updated_at=now,
            unset__error_code=1,
            unset__error_subcode=1,
            unset__error_message=1,
            unset__error_details=1,
            unset__meta_http_status=1,
            unset__fbtrace_id=1,
        )
        message.reload()
        return jsonify({'duplicate': False, 'message': _message_dict(message)}), 201
    except MetaWhatsAppError as exc:
        now = datetime.utcnow()
        uncertain = exc.code == 'network_error'
        failure_update = {
            'set__status': 'unknown' if uncertain else 'failed',
            'set__error_code': exc.code or 'meta_error',
            'set__error_message': str(exc)[:500],
            'set__updated_at': now,
            'set__status_updated_at': now,
        }
        optional_diagnostics = {
            'error_subcode': exc.subcode,
            'error_details': exc.details,
            'meta_http_status': exc.meta_http_status,
            'fbtrace_id': exc.fbtrace_id,
        }
        for field, value in optional_diagnostics.items():
            operation = 'set' if value not in (None, '') else 'unset'
            failure_update[f'{operation}__{field}'] = value if operation == 'set' else 1
        message.update(**failure_update)
        response = {
            'error': str(exc),
            'error_code': exc.code,
            'error_subcode': exc.subcode,
            'error_details': exc.details or None,
            'meta_http_status': exc.meta_http_status,
            'fbtrace_id': exc.fbtrace_id or None,
        }
        return jsonify(response), exc.http_status


@whatsapp_integration_bp.get('/webhook')
def verify_webhook():
    production = _production_request()
    try:
        MetaWhatsAppService(production=production).assert_configured()
    except MetaWhatsAppError:
        return jsonify({'error': 'Webhook is not configured'}), 503
    expected = os.environ.get('META_WA_WEBHOOK_VERIFY_TOKEN', '')
    supplied = request.args.get('hub.verify_token', '')
    if (
        request.args.get('hub.mode') == 'subscribe'
        and expected
        and hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8'))
    ):
        return Response(request.args.get('hub.challenge', ''), mimetype='text/plain')
    return jsonify({'error': 'Webhook verification failed'}), 403


@whatsapp_integration_bp.post('/webhook')
def receive_webhook():
    production = _production_request()
    account = {}
    service = MetaWhatsAppService(production=production)
    try:
        service.assert_configured()
    except MetaWhatsAppError:
        return jsonify({'error': 'Webhook is not configured'}), 503
    if production:
        account = {'waba_id': service.business_account_id, 'phone_number_id': service.phone_number_id}
    if request.content_length and request.content_length > MAX_WEBHOOK_BYTES:
        return jsonify({'error': 'Payload too large'}), 413

    raw_body = request.get_data(cache=True, as_text=False)
    if len(raw_body) > MAX_WEBHOOK_BYTES:
        return jsonify({'error': 'Payload too large'}), 413
    app_secret = os.environ.get('META_WA_APP_SECRET', '')
    phone_number_id = service.phone_number_id
    if not app_secret or not phone_number_id:
        return jsonify({'error': 'Webhook is not configured'}), 503
    signature_header = request.headers.get('X-Hub-Signature-256', '')
    signature_valid = verify_webhook_signature(
        raw_body,
        signature_header,
        app_secret,
    )
    if not signature_valid:
        _log_webhook_signature_rejected(raw_body, signature_header, app_secret)
        return jsonify({'error': 'Invalid webhook signature'}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Invalid JSON payload'}), 400
    payload_hash = hashlib.sha256(raw_body).hexdigest()

    processed = 0
    for event in extract_webhook_events(
        payload,
        expected_phone_number_id=phone_number_id,
        **({'expected_waba_id': account['waba_id']} if production else {}),
    ):
        try:
            WhatsAppWebhookEvent(
                event_key=(f"{account['waba_id']}:{event['event_key']}" if production else event['event_key']),
                event_type=event['event_type'],
                payload_hash=payload_hash,
                meta_message_id=event['meta_message_id'],
                status=event['status'],
                **account,
            ).save(force_insert=True)
            processed += 1
        except NotUniqueError:
            if not production:
                continue
            # A retry can finish a status update interrupted after the insert.
            # Monotonic updates prevent already-applied states from being replayed.
        if event['event_type'] == 'status':
            error_code = event['error_code']
            if production and not (error_code.isascii() and error_code.isdigit()):
                error_code = ''
            _update_message_status(
                event['meta_message_id'],
                event['status'],
                error_code,
                '' if production else event['error_message'],
                **({'account': account} if production else {}),
            )
    return jsonify({'received': True, 'processed': processed})
