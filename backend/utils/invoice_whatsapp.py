"""Fail-closed paid-invoice WhatsApp notification foundation."""
import math
import os
import re
import secrets
from datetime import datetime

from mongoengine.errors import NotUniqueError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from models import (
    Invoice,
    InvoiceLifecycleEvent,
    WhatsAppInvoiceNotification,
)
from utils.env_config import RuntimeConfigurationError, get_app_runtime
from utils.meta_whatsapp_service import MetaWhatsAppError, MetaWhatsAppService


INVOICE_NOTIFICATION_TYPE = 'invoice_paid'
INVOICE_TEMPLATE_NAME = 'priyanka_invoice_paid'
INVOICE_TEMPLATE_LANGUAGE = 'en_US'
STATUS_ORDER = ['pending', 'accepted', 'sent', 'delivered', 'read']
SHARE_CODE_RE = re.compile(r'^[A-Za-z0-9_-]{8}$')


class InvoiceWhatsAppEligibilityError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _enabled(name):
    return os.environ.get(name, '').strip().lower() == 'true'


def _notification_config():
    if not _enabled('WHATSAPP_INVOICE_NOTIFICATIONS_ENABLED'):
        return None
    try:
        runtime = get_app_runtime()
    except RuntimeConfigurationError as exc:
        raise InvoiceWhatsAppEligibilityError('runtime_invalid') from exc
    if runtime != 'production':
        raise InvoiceWhatsAppEligibilityError('production_runtime_required')

    template_name = os.environ.get(
        'META_WA_INVOICE_TEMPLATE_NAME', INVOICE_TEMPLATE_NAME
    ).strip()
    language = os.environ.get(
        'META_WA_INVOICE_TEMPLATE_LANGUAGE', INVOICE_TEMPLATE_LANGUAGE
    ).strip()
    if template_name != INVOICE_TEMPLATE_NAME or language != INVOICE_TEMPLATE_LANGUAGE:
        raise InvoiceWhatsAppEligibilityError('template_configuration_invalid')
    return template_name, language


def normalize_indian_whatsapp_phone(value):
    """Return India E.164 digits accepted by Meta, or None when malformed."""
    raw = str(value or '').strip()
    if not raw or not re.fullmatch(r'[+0-9 ().-]+', raw):
        return None
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in '6789':
        digits = f'91{digits}'
    if not re.fullmatch(r'91[6-9][0-9]{9}', digits):
        return None
    return digits


def _customer_name(customer):
    name = ' '.join(filter(None, [
        str(getattr(customer, 'first_name', '') or '').strip(),
        str(getattr(customer, 'last_name', '') or '').strip(),
    ])).strip()
    return name[:150]


def _eligible_invoice(invoice, bill):
    if not invoice or invoice.invoice_status != 'finalized':
        raise InvoiceWhatsAppEligibilityError('invoice_not_finalized')
    if getattr(bill, 'booking_status', None) != 'service-completed':
        raise InvoiceWhatsAppEligibilityError('bill_not_paid')
    if not str(getattr(bill, 'payment_mode', '') or '').strip():
        raise InvoiceWhatsAppEligibilityError('payment_mode_missing')
    try:
        amount = float(getattr(bill, 'final_amount', 0) or 0)
    except (TypeError, ValueError) as exc:
        raise InvoiceWhatsAppEligibilityError('paid_amount_invalid') from exc
    if not math.isfinite(amount) or amount <= 0:
        raise InvoiceWhatsAppEligibilityError('paid_amount_invalid')

    customer = getattr(bill, 'customer', None)
    if not customer:
        raise InvoiceWhatsAppEligibilityError('customer_missing')
    if getattr(customer, 'whatsapp_consent', False) is not True:
        raise InvoiceWhatsAppEligibilityError('whatsapp_consent_required')
    phone = normalize_indian_whatsapp_phone(getattr(customer, 'mobile', None))
    if not phone:
        raise InvoiceWhatsAppEligibilityError('customer_phone_invalid')
    name = _customer_name(customer)
    if not name:
        raise InvoiceWhatsAppEligibilityError('customer_name_missing')
    invoice_number = str(getattr(invoice, 'invoice_number', '') or '').strip()
    if not invoice_number:
        raise InvoiceWhatsAppEligibilityError('invoice_number_missing')
    return {
        'customer': customer,
        'phone': phone,
        'customer_name': name,
        'paid_amount': f'{amount:.2f}',
        'invoice_number': invoice_number[:50],
    }


def ensure_invoice_share_code(invoice):
    """Atomically create or reuse a finalized invoice's short share code."""
    if not invoice or invoice.invoice_status != 'finalized':
        raise InvoiceWhatsAppEligibilityError('invoice_not_finalized')
    existing = str(getattr(invoice, 'share_code', '') or '')
    if existing:
        return existing

    collection = Invoice._get_collection()
    for _ in range(10):
        candidate = secrets.token_urlsafe(6)
        if not SHARE_CODE_RE.fullmatch(candidate):
            continue
        try:
            updated = collection.find_one_and_update(
                {
                    '_id': invoice.id,
                    'invoice_status': 'finalized',
                    '$or': [
                        {'share_code': {'$exists': False}},
                        {'share_code': None},
                        {'share_code': ''},
                    ],
                },
                {'$set': {
                    'share_code': candidate,
                    'updated_at': datetime.utcnow(),
                }},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            continue
        if updated:
            invoice.share_code = candidate
            return candidate

        invoice.reload()
        existing = str(getattr(invoice, 'share_code', '') or '')
        if existing:
            return existing
        if invoice.invoice_status != 'finalized':
            raise InvoiceWhatsAppEligibilityError('invoice_not_finalized')
    raise RuntimeError('invoice_share_code_unavailable')


def mark_invoice_shared(invoice):
    """Record distribution only after a share response or Meta acceptance."""
    now = datetime.utcnow()
    Invoice.objects(id=invoice.id).update_one(
        set__shared_at=now,
        set__updated_at=now,
    )
    Invoice.objects(id=invoice.id, status='generated').update_one(
        set__status='shared'
    )
    invoice.shared_at = now
    if getattr(invoice, 'status', None) == 'generated':
        invoice.status = 'shared'


def _notification_result(notification, *, duplicate=False):
    result = {'status': notification.status}
    if duplicate:
        result['duplicate'] = True
    if notification.status == 'failed' and notification.last_error_code:
        result['error_code'] = notification.last_error_code
    return result


def _reserve_notification(
    invoice,
    bill,
    customer,
    template_name,
    language,
    *,
    attempt_kind,
    idempotency_key,
):
    notification = WhatsAppInvoiceNotification(
        invoice=invoice,
        bill=bill,
        customer=customer,
        branch=getattr(bill, 'branch', None),
        notification_type=INVOICE_NOTIFICATION_TYPE,
        attempt_kind=attempt_kind,
        idempotency_key=idempotency_key,
        template_name=template_name,
        language=language,
        status='pending',
        attempt_count=1,
    )
    try:
        notification.save(force_insert=True)
        return notification, True
    except NotUniqueError:
        existing = WhatsAppInvoiceNotification.objects(
            invoice=invoice,
            notification_type=INVOICE_NOTIFICATION_TYPE,
            idempotency_key=idempotency_key,
        ).first()
        if not existing:
            raise RuntimeError('invoice_notification_reservation_conflict')
        return existing, False


def _record_lifecycle(notification, event_type):
    event_key = f'invoice-whatsapp:{notification.id}:{event_type}'
    try:
        InvoiceLifecycleEvent(
            event_key=event_key,
            event_type=event_type,
            bill=notification.bill,
            invoice=notification.invoice,
            notification=notification,
            customer=notification.customer,
        ).save(force_insert=True)
    except NotUniqueError:
        pass
    except Exception:
        # Notification state remains authoritative; audit failure must not break billing.
        pass


def _set_notification(notification, **values):
    values['updated_at'] = datetime.utcnow()
    notification.update(**{f'set__{key}': value for key, value in values.items()})
    for key, value in values.items():
        setattr(notification, key, value)


def _mark_failed(notification, error_code):
    safe_code = str(error_code or 'send_failed')[:100]
    _set_notification(notification, status='failed', last_error_code=safe_code)
    _record_lifecycle(notification, 'invoice_whatsapp_failed')
    return _notification_result(notification)


def try_send_paid_invoice_whatsapp(
    invoice,
    bill,
    *,
    attempt_kind='automatic',
    idempotency_key='automatic',
):
    """Reserve and attempt one send without ever raising into invoice finalization."""
    if not _enabled('WHATSAPP_INVOICE_NOTIFICATIONS_ENABLED'):
        return None
    try:
        config = _notification_config()
        eligible = _eligible_invoice(invoice, bill)
        share_code = ensure_invoice_share_code(invoice)
    except InvoiceWhatsAppEligibilityError as exc:
        return {'status': 'skipped', 'reason': exc.code}
    except Exception:
        return {'status': 'failed', 'error_code': 'preparation_failed'}

    template_name, language = config
    try:
        notification, created = _reserve_notification(
            invoice,
            bill,
            eligible['customer'],
            template_name,
            language,
            attempt_kind=attempt_kind,
            idempotency_key=idempotency_key,
        )
    except Exception:
        return {'status': 'failed', 'error_code': 'reservation_failed'}
    if not created:
        return _notification_result(notification, duplicate=True)

    try:
        service = MetaWhatsAppService(production=True)
        approved = any(
            item.get('name') == template_name
            and item.get('language') == language
            and item.get('status') == 'APPROVED'
            and item.get('category') == 'UTILITY'
            for item in service.get_templates(status='APPROVED')
            if isinstance(item, dict)
        )
        if not approved:
            return _mark_failed(notification, 'template_not_approved')
        result = service.send_template(
            eligible['phone'],
            template_name,
            language,
            body_parameters=[
                eligible['customer_name'],
                eligible['paid_amount'],
                eligible['invoice_number'],
            ],
            url_button_parameter=share_code,
        )
        accepted_at = datetime.utcnow()
        _set_notification(
            notification,
            status='accepted',
            meta_message_id=result['message_id'],
            waba_id=service.business_account_id,
            phone_number_id=service.phone_number_id,
            accepted_at=accepted_at,
            last_error_code=None,
        )
        try:
            mark_invoice_shared(invoice)
        except Exception:
            pass
        _record_lifecycle(notification, 'invoice_whatsapp_accepted')
        return _notification_result(notification)
    except MetaWhatsAppError as exc:
        return _mark_failed(notification, exc.code or 'meta_error')
    except Exception:
        return _mark_failed(notification, 'internal_error')


def update_invoice_notification_status(message_id, new_status, error_code='', *, account=None):
    """Apply signed Meta status events monotonically to invoice notifications."""
    if new_status not in STATUS_ORDER and new_status != 'failed':
        return False
    if new_status == 'failed':
        allowed_current = ['pending', 'accepted', 'sent']
    else:
        new_rank = STATUS_ORDER.index(new_status)
        allowed_current = STATUS_ORDER[:new_rank]
    if not allowed_current:
        return False

    now = datetime.utcnow()
    update = {
        'set__status': new_status,
        'set__updated_at': now,
    }
    timestamp_field = {
        'accepted': 'accepted_at',
        'sent': 'sent_at',
        'delivered': 'delivered_at',
        'read': 'read_at',
    }.get(new_status)
    if timestamp_field:
        update[f'set__{timestamp_field}'] = now
    if new_status == 'failed':
        update['set__last_error_code'] = str(error_code or 'delivery_failed')[:100]

    notification = WhatsAppInvoiceNotification.objects(
        meta_message_id=message_id,
        status__in=allowed_current,
        **(account or {}),
    ).modify(new=True, **update)
    if not notification:
        return False
    audit_type = {
        'delivered': 'invoice_whatsapp_delivered',
        'read': 'invoice_whatsapp_read',
        'failed': 'invoice_whatsapp_failed',
    }.get(new_status)
    if audit_type:
        _record_lifecycle(notification, audit_type)
    return True
