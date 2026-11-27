"""Durable queue and status helpers for production WhatsApp campaigns."""
import hashlib
import json
import os
import re
from datetime import datetime, timedelta

from bson import ObjectId
from pymongo import ReturnDocument, UpdateOne

from models import CampaignWhatsAppRecipient, OfferCampaign


CAMPAIGN_TEMPLATE_NAME = 'priyanka_promotional_offer'
CAMPAIGN_TEMPLATE_LANGUAGE = 'en_US'
DEFAULT_BATCH_SIZE = 20
MAX_PROCESSING_BATCH_SIZE = 100
PERSISTENCE_CHUNK_SIZE = 500
WORKER_LEASE_SECONDS = 600
STATUS_ORDER = ['accepted', 'sent', 'delivered', 'read']
PAUSE_ERROR_CODES = {
    '4', '80007', '130429', '131031', '131042', '131048', '131049',
    '131056', 'network_error', 'missing_message_id',
    'invalid_response', 'sender_not_connected', 'phone_waba_mismatch',
    'configuration_missing', 'configuration_invalid',
}


def campaign_flag_enabled(name):
    return os.environ.get(name, '').strip().lower() == 'true'


def campaign_batch_size():
    """Return an internal processing size, never a campaign recipient limit."""
    try:
        configured = int(os.environ.get('WHATSAPP_CAMPAIGN_BATCH_SIZE', DEFAULT_BATCH_SIZE))
    except (TypeError, ValueError):
        configured = DEFAULT_BATCH_SIZE
    return max(1, min(configured, MAX_PROCESSING_BATCH_SIZE))


def normalize_indian_campaign_phone(value):
    raw = str(value or '').strip()
    if not raw or not re.fullmatch(r'[+0-9 ().-]+', raw):
        return None
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in '6789':
        digits = f'91{digits}'
    return digits if re.fullmatch(r'91[6-9][0-9]{9}', digits) else None


def build_campaign_request_hash(*, customer_ids, media_asset_id, branch_id, message_text):
    payload = {
        'customer_ids': sorted(customer_ids),
        'media_asset_id': media_asset_id,
        'branch_id': branch_id,
        'message_text': message_text,
        'template_name': CAMPAIGN_TEMPLATE_NAME,
        'language_code': CAMPAIGN_TEMPLATE_LANGUAGE,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _reference_id(value):
    return ObjectId(str(getattr(value, 'id', value)))


def reserve_campaign_recipients(campaign, eligible, media_asset, account):
    """Idempotently persist every eligible recipient in bounded DB-write chunks."""
    collection = CampaignWhatsAppRecipient._get_collection()
    now = datetime.utcnow()
    created_count = 0
    operations = []

    def flush():
        nonlocal created_count, operations
        if not operations:
            return
        result = collection.bulk_write(operations, ordered=False)
        created_count += int(result.upserted_count or 0)
        operations = []

    campaign_id = _reference_id(campaign)
    media_asset_id = _reference_id(media_asset)
    for customer, normalized_phone in eligible:
        customer_id = _reference_id(customer)
        branch = campaign.branch or getattr(customer, 'branch', None)
        document = {
            '_id': ObjectId(),
            'campaign': campaign_id,
            'customer': customer_id,
            'branch': _reference_id(branch) if branch else None,
            'waba_id': account['waba_id'],
            'phone_number_id': account['phone_number_id'],
            'template_name': CAMPAIGN_TEMPLATE_NAME,
            'language_code': CAMPAIGN_TEMPLATE_LANGUAGE,
            'media_asset': media_asset_id,
            'normalized_recipient': normalized_phone,
            'status': 'queued',
            'attempt_count': 0,
            'created_at': now,
            'updated_at': now,
            'status_updated_at': now,
        }
        operations.append(UpdateOne(
            {
                'campaign': campaign_id,
                'customer': customer_id,
                'template_name': CAMPAIGN_TEMPLATE_NAME,
            },
            {'$setOnInsert': document},
            upsert=True,
        ))
        if len(operations) >= PERSISTENCE_CHUNK_SIZE:
            flush()
    flush()
    return {
        'created_count': created_count,
        'duplicate_count': max(0, len(eligible) - created_count),
    }


def refresh_campaign_aggregates(campaign):
    records = CampaignWhatsAppRecipient.objects(campaign=campaign)
    queued = records.filter(status='queued').count()
    processing = records.filter(status='processing').count()
    accepted = records.filter(status__in=['accepted', 'sent', 'delivered', 'read']).count()
    sent = records.filter(status__in=['sent', 'delivered', 'read']).count()
    delivered = records.filter(status__in=['delivered', 'read']).count()
    read = records.filter(status='read').count()
    failed = records.filter(status='failed').count()
    unknown = records.filter(status='unknown').count()
    eligible = int(getattr(campaign, 'eligible_count', 0) or 0)
    paused = bool(getattr(campaign, 'pause_reason', '')) and queued > 0

    if paused:
        campaign_status = 'paused'
    elif queued:
        campaign_status = 'queued'
    elif processing:
        campaign_status = 'processing'
    elif eligible and read >= eligible:
        campaign_status = 'read'
    elif eligible and delivered >= eligible:
        campaign_status = 'delivered'
    elif eligible and failed + unknown >= eligible:
        campaign_status = 'failed' if failed >= eligible else 'attention_required'
    elif eligible:
        campaign_status = 'in_progress'
    else:
        campaign_status = 'failed' if getattr(campaign, 'excluded_count', 0) else 'pending'

    now = datetime.utcnow()
    values = {
        'queued_count': queued,
        'processing_count': processing,
        'accepted_count': accepted,
        'sent_count': sent,
        'delivered_count': delivered,
        'read_count': read,
        'failed_count': failed,
        'unknown_count': unknown,
        'status': campaign_status,
        'updated_at': now,
    }
    campaign.update(**{f'set__{field}': value for field, value in values.items()})
    for field, value in values.items():
        setattr(campaign, field, value)
    return campaign


def claim_campaign(worker_id, campaign_id=None):
    now = datetime.utcnow()
    query = {
        'queued_count': {'$gt': 0},
        'status': {'$in': ['queued', 'processing', 'in_progress']},
        '$or': [
            {'worker_lease_expires_at': {'$exists': False}},
            {'worker_lease_expires_at': None},
            {'worker_lease_expires_at': {'$lte': now}},
        ],
    }
    if campaign_id:
        query['_id'] = ObjectId(str(campaign_id))
    document = OfferCampaign._get_collection().find_one_and_update(
        query,
        {'$set': {
            'worker_lease_id': worker_id,
            'worker_lease_expires_at': now + timedelta(seconds=WORKER_LEASE_SECONDS),
            'status': 'processing',
            'updated_at': now,
        }},
        sort=[('created_at', 1)],
        return_document=ReturnDocument.AFTER,
    )
    return OfferCampaign.objects(id=document['_id']).first() if document else None


def expire_ambiguous_recipient_claims(campaign):
    """Never resend a claim whose worker died at an unknown point in the send."""
    now = datetime.utcnow()
    result = CampaignWhatsAppRecipient._get_collection().update_many(
        {
            'campaign': _reference_id(campaign),
            'status': 'processing',
            'lease_expires_at': {'$lte': now},
        },
        {
            '$set': {
                'status': 'unknown',
                'error_code': 'worker_interrupted',
                'error_message': 'Worker stopped while delivery outcome was unknown.',
                'updated_at': now,
                'status_updated_at': now,
            },
            '$unset': {'worker_lease_id': '', 'lease_expires_at': ''},
        },
    )
    return result.modified_count


def claim_queued_recipient(campaign, worker_id):
    now = datetime.utcnow()
    document = CampaignWhatsAppRecipient._get_collection().find_one_and_update(
        {'campaign': _reference_id(campaign), 'status': 'queued'},
        {
            '$set': {
                'status': 'processing',
                'worker_lease_id': worker_id,
                'lease_expires_at': now + timedelta(seconds=WORKER_LEASE_SECONDS),
                'claimed_at': now,
                'updated_at': now,
                'status_updated_at': now,
            },
            '$inc': {'attempt_count': 1},
        },
        sort=[('created_at', 1)],
        return_document=ReturnDocument.AFTER,
    )
    return CampaignWhatsAppRecipient.objects(id=document['_id']).first() if document else None


def set_recipient_status(recipient, status, *, message_id=None, error_code='', error_message=''):
    now = datetime.utcnow()
    update = {
        'set__status': status,
        'set__updated_at': now,
        'set__status_updated_at': now,
        'unset__worker_lease_id': 1,
        'unset__lease_expires_at': 1,
    }
    if message_id:
        update['set__meta_message_id'] = message_id
    update[('set__' if error_code else 'unset__') + 'error_code'] = (
        str(error_code)[:100] if error_code else 1
    )
    update[('set__' if error_message else 'unset__') + 'error_message'] = (
        str(error_message)[:500] if error_message else 1
    )
    recipient.update(**update)
    recipient.status = status
    if message_id:
        recipient.meta_message_id = message_id
    recipient.error_code = str(error_code)[:100] if error_code else None
    recipient.error_message = str(error_message)[:500] if error_message else None


def release_campaign_lease(campaign):
    campaign.update(
        unset__worker_lease_id=1,
        unset__worker_lease_expires_at=1,
        set__updated_at=datetime.utcnow(),
    )


def pause_campaign(campaign, error_code, error_message):
    now = datetime.utcnow()
    code = str(error_code or 'processing_paused')[:100]
    reason = str(error_message or 'Campaign processing paused.')[:500]
    campaign.update(
        set__status='paused',
        set__pause_code=code,
        set__pause_reason=reason,
        set__paused_at=now,
        set__updated_at=now,
        unset__worker_lease_id=1,
        unset__worker_lease_expires_at=1,
    )
    campaign.status = 'paused'
    campaign.pause_code = code
    campaign.pause_reason = reason


def resume_campaign(campaign):
    campaign.update(
        set__status='queued',
        set__updated_at=datetime.utcnow(),
        unset__pause_code=1,
        unset__pause_reason=1,
        unset__paused_at=1,
        unset__worker_lease_id=1,
        unset__worker_lease_expires_at=1,
    )
    campaign.status = 'queued'
    campaign.pause_code = None
    campaign.pause_reason = None
    campaign.paused_at = None


def campaign_error_requires_pause(error):
    code = str(getattr(error, 'code', '') or '')
    return (
        code in PAUSE_ERROR_CODES
        or getattr(error, 'http_status', None) == 429
        or (getattr(error, 'meta_http_status', None) or 0) == 429
    )


def update_campaign_recipient_status(
    message_id, new_status, error_code='', error_message='', *, account=None,
):
    if new_status not in STATUS_ORDER and new_status != 'failed':
        return False
    if new_status == 'failed':
        allowed_current = ['accepted', 'sent', 'unknown']
    else:
        new_rank = STATUS_ORDER.index(new_status)
        allowed_current = STATUS_ORDER[:new_rank]
        allowed_current.append('unknown')
    if not allowed_current:
        return False

    now = datetime.utcnow()
    update = {
        'set__status': new_status,
        'set__updated_at': now,
        'set__status_updated_at': now,
    }
    if new_status == 'failed':
        update['set__error_code'] = str(error_code or 'delivery_failed')[:100]
        update['set__error_message'] = str(error_message or '')[:500]
    recipient = CampaignWhatsAppRecipient.objects(
        meta_message_id=message_id,
        status__in=allowed_current,
        **(account or {}),
    ).modify(new=True, **update)
    if not recipient:
        return False
    refresh_campaign_aggregates(recipient.campaign)
    return True
