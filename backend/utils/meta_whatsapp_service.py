"""Server-side Meta WhatsApp Cloud API client."""
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass

import requests


PHONE_RE = re.compile(r'^\d{8,15}$')
VERSION_RE = re.compile(r'^v\d+\.\d+$')
BEARER_TOKEN_RE = re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~-]+')
EMAIL_RE = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
PHONE_OR_ID_RE = re.compile(r'(?<!\w)\+?\d(?:[\s().-]*\d){7,19}(?!\w)')
TRACE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{1,200}$')

SALON_DEMO_WABA_ID = '1051521404559842'
SALON_PRODUCTION_WABA_ID = '4800759546811980'
SALON_PRODUCTION_PHONE_NUMBER_ID = '1521113507744203'
MEDISCRIPT_WABA_ID = '1839181954189408'
MEDISCRIPT_PHONE_NUMBER_ID = '1418048524730737'


def sanitize_meta_error_text(value, access_token=''):
    """Keep diagnostic text while removing credentials and personal identifiers."""
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, separators=(',', ':'))
    else:
        text = str(value)
    if access_token:
        text = text.replace(access_token, '[redacted]')
    text = BEARER_TOKEN_RE.sub('Bearer [redacted]', text)
    text = EMAIL_RE.sub('[redacted]', text)
    text = PHONE_OR_ID_RE.sub('[redacted]', text)
    return text[:500]


def sanitize_meta_trace_id(value):
    trace_id = str(value or '').strip()
    return trace_id if TRACE_ID_RE.fullmatch(trace_id) else ''


class MetaWhatsAppError(RuntimeError):
    def __init__(
        self,
        message,
        *,
        http_status=502,
        code=None,
        subcode=None,
        meta_http_status=None,
        details='',
        fbtrace_id='',
    ):
        super().__init__(message)
        self.http_status = http_status
        self.code = str(code)[:100] if code is not None else None
        self.subcode = str(subcode)[:100] if subcode is not None else None
        try:
            parsed_meta_status = int(meta_http_status) if meta_http_status is not None else None
        except (TypeError, ValueError):
            parsed_meta_status = None
        self.meta_http_status = (
            parsed_meta_status if parsed_meta_status and 100 <= parsed_meta_status <= 599 else None
        )
        self.details = sanitize_meta_error_text(details)
        self.fbtrace_id = sanitize_meta_trace_id(fbtrace_id)


@dataclass(frozen=True)
class TestRecipient:
    recipient_id: str
    label: str
    phone: str

    def public_dict(self):
        return {
            'id': self.recipient_id,
            'label': self.label,
            'masked_phone': mask_phone(self.phone),
        }


def mask_phone(phone):
    digits = re.sub(r'\D', '', str(phone or ''))
    if not digits:
        return ''
    return f"{'*' * max(4, len(digits) - 4)}{digits[-4:]}"


def load_test_recipients(raw_value=None, *, production=False):
    raw = raw_value if raw_value is not None else os.environ.get('META_WA_TEST_RECIPIENTS_JSON', '')
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError('META_WA_TEST_RECIPIENTS_JSON must be valid JSON.') from exc
    if not isinstance(parsed, list):
        raise RuntimeError('META_WA_TEST_RECIPIENTS_JSON must contain a JSON array.')

    recipients = []
    seen_ids = set()
    seen_phones = set()
    for item in parsed:
        if not isinstance(item, dict):
            raise RuntimeError('Each Meta test recipient must be a JSON object.')
        recipient_id = str(item.get('id', '')).strip()
        label = str(item.get('label', '')).strip()
        raw_phone = str(item.get('phone', '')).strip()
        phone = re.sub(r'\D', '', raw_phone)
        if not recipient_id or not label or not PHONE_RE.fullmatch(phone):
            raise RuntimeError('Every Meta test recipient requires id, label and an E.164 phone number.')
        if production and (
            item.get('opted_in') is not True
            or not re.fullmatch(r'\+?[1-9][0-9]{7,14}', raw_phone)
            or len(recipient_id) > 64
            or len(label) > 100
        ):
            raise RuntimeError('Production test recipients require explicit opt-in and an E.164 number.')
        if recipient_id in seen_ids or phone in seen_phones:
            raise RuntimeError('Meta test recipient ids and phone numbers must be unique.')
        seen_ids.add(recipient_id)
        seen_phones.add(phone)
        recipients.append(TestRecipient(recipient_id, label, phone))
    return recipients


def verify_webhook_signature(raw_body, signature_header, app_secret):
    if (
        not app_secret
        or not isinstance(signature_header, str)
        or not re.fullmatch(r'sha256=[0-9a-fA-F]{64}', signature_header)
    ):
        return False
    supplied = signature_header.split('=', 1)[1].lower()
    expected = hmac.new(
        app_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(supplied, expected)


def extract_webhook_events(
    payload, expected_phone_number_id=None, expected_waba_id=SALON_DEMO_WABA_ID,
):
    """Return delivery/inbound metadata without retaining inbound message content."""
    if not isinstance(payload, dict) or payload.get('object') != 'whatsapp_business_account':
        return []
    if (
        not isinstance(expected_phone_number_id, str)
        or not expected_phone_number_id.isascii()
        or not expected_phone_number_id.isdecimal()
        or expected_phone_number_id == MEDISCRIPT_PHONE_NUMBER_ID
    ):
        return []
    entries = payload.get('entry')
    if not isinstance(entries, list):
        return []

    events = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        waba_id = entry.get('id')
        if waba_id == MEDISCRIPT_WABA_ID or waba_id != expected_waba_id:
            continue
        changes = entry.get('changes')
        if not isinstance(changes, list):
            continue
        for change in changes:
            if not isinstance(change, dict) or change.get('field') != 'messages':
                continue
            value = change.get('value')
            if not isinstance(value, dict) or value.get('messaging_product') != 'whatsapp':
                continue
            metadata = value.get('metadata')
            if not isinstance(metadata, dict):
                continue
            phone_number_id = metadata.get('phone_number_id')
            if phone_number_id == MEDISCRIPT_PHONE_NUMBER_ID or phone_number_id != expected_phone_number_id:
                continue
            statuses = value.get('statuses', [])
            messages = value.get('messages', [])
            if not isinstance(statuses, list) or not isinstance(messages, list):
                continue
            for status in statuses:
                if not isinstance(status, dict) or not isinstance(status.get('id'), str) or not status['id']:
                    continue
                message_id = str(status['id'])
                status_name = str(status.get('status', 'unknown')).lower()
                timestamp = str(status.get('timestamp', ''))
                errors = status.get('errors', [])
                if not isinstance(errors, list) or any(not isinstance(error, dict) for error in errors):
                    continue
                error = errors[0] if errors else {}
                event_source = f'status:{message_id}:{status_name}:{timestamp}'
                events.append({
                    'event_key': hashlib.sha256(event_source.encode('utf-8')).hexdigest(),
                    'event_type': 'status',
                    'meta_message_id': message_id,
                    'status': status_name,
                    'error_code': str(error.get('code', ''))[:100],
                    'error_message': sanitize_meta_error_text(
                        error.get('title') or error.get('message') or ''
                    ),
                })
            for message in messages:
                if not isinstance(message, dict) or not isinstance(message.get('id'), str) or not message['id']:
                    continue
                message_id = str(message['id'])
                event_source = f'message:{message_id}'
                events.append({
                    'event_key': hashlib.sha256(event_source.encode('utf-8')).hexdigest(),
                    'event_type': 'inbound',
                    'meta_message_id': message_id,
                    'status': 'received',
                    'error_code': '',
                    'error_message': '',
                })
    return events


class MetaWhatsAppService:
    REQUIRED_ENV = (
        'META_WA_ACCESS_TOKEN',
        'META_WA_PHONE_NUMBER_ID',
        'META_WA_BUSINESS_ACCOUNT_ID',
        'META_GRAPH_API_VERSION',
    )

    WEBHOOK_ENV = ('META_WA_APP_SECRET', 'META_WA_WEBHOOK_VERIFY_TOKEN')

    def __init__(self, *, request_func=None, production=False):
        self.production = production
        self.access_token = os.environ.get('META_WA_ACCESS_TOKEN', '').strip()
        self.phone_number_id = os.environ.get('META_WA_PHONE_NUMBER_ID', '').strip()
        self.business_account_id = os.environ.get('META_WA_BUSINESS_ACCOUNT_ID', '').strip()
        self.graph_version = os.environ.get('META_GRAPH_API_VERSION', '').strip()
        self.request_func = request_func or requests.request

    def missing_configuration(self):
        required = self.REQUIRED_ENV + (self.WEBHOOK_ENV if self.production else ())
        return [name for name in required if not os.environ.get(name, '').strip()]

    def assert_configured(self):
        missing = self.missing_configuration()
        if missing:
            raise MetaWhatsAppError(
                f"Meta WhatsApp is not configured. Missing: {', '.join(missing)}",
                http_status=503,
                code='configuration_missing',
            )
        if not VERSION_RE.fullmatch(self.graph_version):
            raise MetaWhatsAppError(
                'META_GRAPH_API_VERSION is invalid.',
                http_status=503,
                code='configuration_invalid',
            )
        if (
            self.production and (
                self.business_account_id != SALON_PRODUCTION_WABA_ID
                or self.phone_number_id != SALON_PRODUCTION_PHONE_NUMBER_ID
            )
        ) or (
            not self.production and (
                self.business_account_id == SALON_PRODUCTION_WABA_ID
                or self.phone_number_id == SALON_PRODUCTION_PHONE_NUMBER_ID
            )
        ):
            raise MetaWhatsAppError(
                'WhatsApp account does not match this runtime.',
                http_status=503,
                code='configuration_invalid',
            )
        if self.production and any(
            os.environ[name] != os.environ[name].strip() for name in self.WEBHOOK_ENV
        ):
            raise MetaWhatsAppError(
                'WhatsApp webhook configuration contains surrounding whitespace.',
                http_status=503,
                code='configuration_invalid',
            )

    @property
    def base_url(self):
        self.assert_configured()
        return f'https://graph.facebook.com/{self.graph_version}'

    def _request(self, method, path, *, params=None, payload=None, upload=None):
        self.assert_configured()
        headers = {'Authorization': f'Bearer {self.access_token}'}
        if upload is None:
            headers['Content-Type'] = 'application/json'
            request_body = {'json': payload}
        else:
            data, content_type = upload
            request_body = {
                'data': {'messaging_product': 'whatsapp', 'type': content_type},
                'files': {'file': ('image', data, content_type)},
            }
        try:
            response = self.request_func(
                method,
                f'{self.base_url}/{path.lstrip("/")}',
                headers=headers,
                params=params,
                **request_body,
                **({'allow_redirects': False} if self.production else {}),
                timeout=15,
            )
        except requests.RequestException as exc:
            raise MetaWhatsAppError(
                'Meta Graph API could not be reached.',
                http_status=502,
                code='network_error',
            ) from exc

        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code >= 400 or (self.production and response.status_code >= 300):
            error = body.get('error', {}) if isinstance(body, dict) else {}
            if not isinstance(error, dict):
                error = {}
            if self.production:
                code = error.get('code')
                raise MetaWhatsAppError(
                    'Meta Graph API rejected the request.',
                    code=code if type(code) is int else f'http_{response.status_code}',
                    meta_http_status=response.status_code,
                )
            error_data = error.get('error_data', {})
            if not isinstance(error_data, dict):
                error_data = {}
            message = sanitize_meta_error_text(
                error.get('message') or 'Meta Graph API rejected the request.',
                self.access_token,
            )
            details = sanitize_meta_error_text(
                error_data.get('details') or error.get('error_user_msg') or '',
                self.access_token,
            )
            headers = getattr(response, 'headers', {}) or {}
            fbtrace_id = sanitize_meta_trace_id(
                error.get('fbtrace_id') or headers.get('x-fb-trace-id', '')
            )
            raise MetaWhatsAppError(
                message,
                http_status=502,
                code=error.get('code') or f'http_{response.status_code}',
                subcode=error.get('error_subcode'),
                meta_http_status=response.status_code,
                details=details,
                fbtrace_id=fbtrace_id,
            )
        if not isinstance(body, dict):
            raise MetaWhatsAppError('Meta Graph API returned an invalid response.', code='invalid_response')
        return body

    def get_sender(self):
        fields = 'display_phone_number,verified_name,quality_rating'
        body = self._request(
            'GET',
            self.phone_number_id,
            params={'fields': f'{fields},status' if self.production else fields},
        )
        if self.production and str(body.get('id', '')) != self.phone_number_id:
            raise MetaWhatsAppError('Meta returned an unexpected sender.', code='sender_mismatch')
        return {
            'id': str(body.get('id', '')),
            'display_phone_number': (
                str(body.get('display_phone_number', '')) if self.production
                else mask_phone(body.get('display_phone_number', ''))
            ),
            'verified_name': str(body.get('verified_name', '')),
            'quality_rating': str(body.get('quality_rating', 'UNKNOWN')),
            'graph_version': self.graph_version,
            **({'phone_status': str(body.get('status', 'UNKNOWN')).upper()}
               if self.production else {}),
        }

    def get_templates(self, status=None, *, first_page=False):
        fields = 'id,name,status,category,language'
        params = {'fields': f'{fields},components' if self.production else fields, 'limit': 100}
        if status:
            params['status'] = status
        templates = []
        seen_cursors = set()
        for _ in range(20):
            body = self._request(
                'GET', f'{self.business_account_id}/message_templates', params=params.copy(),
            )
            if not isinstance(body.get('data'), list):
                raise MetaWhatsAppError('Meta returned an invalid template list.', code='invalid_response')
            for item in body['data']:
                if not isinstance(item, dict):
                    continue
                template = {
                    'id': str(item.get('id', '')),
                    'name': str(item.get('name', '')),
                    'status': str(item.get('status', 'UNKNOWN')).upper(),
                    'category': str(item.get('category', 'UNKNOWN')).upper(),
                    'language': str(item.get('language', '')),
                }
                if self.production:
                    components = item.get('components')
                    template['components'] = [
                        {key: value for key, value in component.items()
                         if key in {'type', 'format', 'text'} and isinstance(value, str)}
                        for component in components if isinstance(component, dict)
                    ] if isinstance(components, list) else None
                if not status or template['status'] == status:
                    templates.append(template)
            paging = body.get('paging') or {}
            if first_page or not self.production:
                return templates
            if not isinstance(paging, dict):
                break
            if not paging.get('next'):
                return templates
            cursors = paging.get('cursors')
            cursor = cursors.get('after') if isinstance(cursors, dict) else None
            if not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
                break
            seen_cursors.add(cursor)
            params['after'] = cursor
        raise MetaWhatsAppError('Meta template pagination could not be completed.', code='invalid_response')

    def get_business(self):
        body = self._request('GET', self.business_account_id, params={'fields': 'id,name'})
        if str(body.get('id', '')) != self.business_account_id:
            raise MetaWhatsAppError('Meta returned an unexpected account.', code='account_mismatch')
        return str(body.get('name', ''))

    def has_webhook_subscriptions(self):
        body = self._request('GET', f'{self.business_account_id}/subscribed_apps')
        if not isinstance(body.get('data'), list):
            raise MetaWhatsAppError('Meta returned an invalid subscription list.', code='invalid_response')
        return bool(body['data'])

    def upload_image(self, data, content_type):
        body = self._request('POST', f'{self.phone_number_id}/media', upload=(data, content_type))
        media_id = body.get('id')
        if not isinstance(media_id, str) or not re.fullmatch(r'[0-9]{1,40}', media_id):
            raise MetaWhatsAppError('Meta returned no valid media id.', code='missing_media_id')
        return media_id

    def send_template(self, recipient_phone, template_name, language_code, *, media_id=None):
        body = self._request(
            'POST',
            f'{self.phone_number_id}/messages',
            payload={
                'messaging_product': 'whatsapp',
                'to': recipient_phone,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': language_code},
                    **({'components': [{
                        'type': 'header',
                        'parameters': [{'type': 'image', 'image': {'id': media_id}}],
                    }]} if media_id else {}),
                },
            },
        )
        messages = body.get('messages') or []
        message_id = (
            messages[0].get('id')
            if isinstance(messages, list) and messages and isinstance(messages[0], dict)
            else None
        )
        if not isinstance(message_id, str) or not message_id or len(message_id) > 200:
            raise MetaWhatsAppError('Meta accepted no message id.', code='missing_message_id')
        return {'message_id': message_id, 'status': 'accepted'}
