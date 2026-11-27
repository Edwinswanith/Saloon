"""Production WhatsApp integration contract tests with mocked external I/O."""
import hashlib
import hmac
import json
import logging
import os
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask
from PIL import Image, PngImagePlugin
from werkzeug.datastructures import FileStorage

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'synthetic-production-test-jwt-secret')

from routes import whatsapp_integration_routes as routes
from services.r2_media_service import R2MediaConfigurationError, R2MediaService
from utils import whatsapp_auth
from utils.image_validation import (
    MAX_IMAGE_BYTES,
    ImageValidationError,
    build_media_object_key,
    normalize_uploaded_image,
)
from utils.meta_whatsapp_service import (
    MetaWhatsAppError,
    MetaWhatsAppService,
    SALON_DEMO_PHONE_NUMBER_ID,
    SALON_DEMO_WABA_ID,
    SALON_PRODUCTION_PHONE_NUMBER_ID,
    SALON_PRODUCTION_WABA_ID,
)


OWNER_ID = '000000000000000000000001'
API = '/api/integrations/whatsapp'
SYNTHETIC_SECRET = 'synthetic-production-app-secret'
ENV = {
    'APP_RUNTIME': 'production',
    'META_GRAPH_API_VERSION': 'v26.0',
    'META_WA_ACCESS_TOKEN': 'synthetic-access-token-never-log',
    'META_WA_PHONE_NUMBER_ID': SALON_PRODUCTION_PHONE_NUMBER_ID,
    'META_WA_BUSINESS_ACCOUNT_ID': SALON_PRODUCTION_WABA_ID,
    'META_WA_APP_SECRET': SYNTHETIC_SECRET,
    'META_WA_WEBHOOK_VERIFY_TOKEN': 'synthetic-verify-token',
    'META_WA_TEST_RECIPIENTS_JSON': json.dumps([{
        'id': 'owner-test',
        'label': 'Owner test',
        'phone': '+12025550110',
        'opted_in': True,
    }]),
    'WHATSAPP_PRODUCTION_BILLING_VERIFIED': 'false',
    'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'false',
    'WHATSAPP_PRODUCTION_TEST_ENABLED': 'false',
    'WHATSAPP_PRODUCTION_SEND_ENABLED': 'false',
}
TEMPLATE = {
    'id': '123',
    'name': 'appointment_confirmation',
    'status': 'APPROVED',
    'category': 'UTILITY',
    'language': 'en_US',
    'components': [{'type': 'BODY', 'text': 'Appointment confirmed'}],
}
R2_ENV = {
    'APP_RUNTIME': 'production',
    'R2_ACCESS_KEY_ID': 'synthetic-access-key',
    'R2_SECRET_ACCESS_KEY': 'synthetic-secret-key',
    'R2_ENDPOINT': 'https://example-account.r2.cloudflarestorage.com',
    'R2_BUCKET_NAME': 'airalexo-salon-media-production',
}


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.headers = {}

    def json(self):
        return self._body


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(self.format(record))


def image_upload(raw, filename='promotion.jpg'):
    return FileStorage(stream=BytesIO(raw), filename=filename)


class ProductionMediaSecurityTests(unittest.TestCase):
    def test_valid_image_is_normalized_without_png_text_metadata(self):
        image = Image.new('RGB', (40, 30), (25, 130, 115))
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('private-note', 'must-be-removed')
        output = BytesIO()
        image.save(output, format='PNG', pnginfo=metadata)

        normalized = normalize_uploaded_image(
            image_upload(output.getvalue(), 'promotion.png')
        )

        self.assertEqual(normalized.content_type, 'image/png')
        self.assertNotIn(b'must-be-removed', normalized.data)
        self.assertLessEqual(normalized.byte_size, MAX_IMAGE_BYTES)

    def test_file_type_and_size_are_validated_from_content(self):
        output = BytesIO()
        Image.new('RGB', (10, 10)).save(output, format='GIF')
        with self.assertRaises(ImageValidationError):
            normalize_uploaded_image(image_upload(output.getvalue(), 'fake.jpg'))
        with self.assertRaises(ImageValidationError) as oversized:
            normalize_uploaded_image(image_upload(b'x' * (MAX_IMAGE_BYTES + 1)))
        self.assertEqual(oversized.exception.status_code, 413)

    def test_production_storage_rejects_demo_runtime_and_bucket(self):
        with self.assertRaises(R2MediaConfigurationError):
            R2MediaService(
                client=MagicMock(),
                environ={**R2_ENV, 'APP_RUNTIME': 'demo'},
                production=True,
            )
        with self.assertRaises(R2MediaConfigurationError):
            R2MediaService(
                client=MagicMock(),
                environ={**R2_ENV, 'R2_BUCKET_NAME': 'airalexo-salon-media-demo'},
                production=True,
            )

    def test_production_object_keys_and_uploads_are_private(self):
        client = MagicMock()
        client.put_object.return_value = {'ETag': '"safe-etag"'}
        image = SimpleNamespace(
            data=b'normalized-image',
            byte_size=16,
            content_type='image/jpeg',
            sha256_hex=hashlib.sha256(b'normalized-image').hexdigest(),
        )
        key = build_media_object_key('jpg', production=True)

        result = R2MediaService(
            client=client,
            environ=R2_ENV,
            production=True,
        ).put_image(key, image)

        self.assertRegex(key, r'^production/media/[0-9a-f]{32}\.jpg$')
        self.assertEqual(result.etag, 'safe-etag')
        call = client.put_object.call_args.kwargs
        self.assertEqual(call['CacheControl'], 'private, no-store')
        self.assertNotIn('ACL', call)


class ProductionWhatsAppTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, ENV, clear=True))
        self.current_user = self.enterContext(patch.object(
            whatsapp_auth,
            'get_current_user',
            return_value={'role': 'owner', 'user_id': OWNER_ID},
        ))
        self.owner_query = self.enterContext(patch.object(whatsapp_auth.Owner, 'objects'))
        self.owner_query.return_value.first.return_value = object()
        self.is_demo = self.enterContext(patch.object(
            whatsapp_auth,
            'is_demo_user',
            return_value=False,
        ))
        self.graph = self.enterContext(patch('requests.request', side_effect=self.graph_response))

        app = Flask(__name__)
        app.register_blueprint(routes.whatsapp_integration_bp, url_prefix=API)
        app.testing = True
        self.client = app.test_client()

    def graph_response(self, method, url, **kwargs):
        resource = url.rstrip('/').split('/')[-1]
        if resource in {SALON_PRODUCTION_PHONE_NUMBER_ID, SALON_DEMO_PHONE_NUMBER_ID}:
            return FakeResponse(200, {
                'id': resource,
                'verified_name': (
                    'Priyanka Nature Cure'
                    if resource == SALON_PRODUCTION_PHONE_NUMBER_ID
                    else 'AiraLexo Demo'
                ),
                'display_phone_number': '+1 202 555 0110',
                'quality_rating': 'GREEN',
                'status': 'CONNECTED',
            })
        if resource == SALON_PRODUCTION_WABA_ID:
            return FakeResponse(200, {
                'id': resource,
                'name': 'Priyanka Nature Cure',
            })
        if resource == 'message_templates':
            return FakeResponse(200, {'data': [TEMPLATE]})
        if resource == 'phone_numbers':
            return FakeResponse(200, {
                'data': [{'id': SALON_PRODUCTION_PHONE_NUMBER_ID}],
            })
        if resource == 'subscribed_apps':
            return FakeResponse(200, {'data': [{'id': 'synthetic-app'}]})
        if resource == 'messages' and method == 'POST':
            return FakeResponse(200, {'messages': [{'id': 'wamid.synthetic.accepted'}]})
        raise AssertionError(f'Unexpected mocked Meta resource: {resource}')

    @staticmethod
    def controlled_payload(recipient_id='owner-test'):
        return {
            'request_id': '00000000-0000-4000-8000-000000000001',
            'recipient_id': recipient_id,
            'template_name': TEMPLATE['name'],
            'language': TEMPLATE['language'],
        }

    @staticmethod
    def pending_message():
        message = SimpleNamespace(
            client_request_id='00000000-0000-4000-8000-000000000001',
            recipient_id='owner-test',
            recipient_label='Owner test',
            recipient_last4='0110',
            template_name=TEMPLATE['name'],
            language_code=TEMPLATE['language'],
            waba_id=SALON_PRODUCTION_WABA_ID,
            phone_number_id=SALON_PRODUCTION_PHONE_NUMBER_ID,
            media_asset_id='',
            send_kind='controlled_test',
            meta_message_id=None,
            status='pending',
            error_code=None,
            error_subcode=None,
            error_message=None,
            error_details=None,
            meta_http_status=None,
            fbtrace_id=None,
            sent_by_owner_id=OWNER_ID,
            created_at=None,
            updated_at=None,
        )

        def update(**operations):
            for operation, value in operations.items():
                if operation.startswith('set__'):
                    setattr(message, operation[5:], value)
                elif operation.startswith('unset__'):
                    setattr(message, operation[7:], None)

        message.update = update
        message.reload = lambda: None
        return message

    def test_owner_authentication_is_required(self):
        self.current_user.return_value = None
        self.assertEqual(self.client.get(API + '/status').status_code, 401)

        self.current_user.return_value = {'role': 'manager', 'user_id': OWNER_ID}
        self.assertEqual(self.client.get(API + '/status').status_code, 403)
        self.graph.assert_not_called()

    def test_invalid_runtime_fails_closed_without_meta_access(self):
        with patch.dict(os.environ, {'APP_RUNTIME': 'staging'}):
            response = self.client.get(API + '/status')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()['error_code'], 'runtime_invalid')
        self.graph.assert_not_called()

    def test_active_production_owner_is_required(self):
        self.is_demo.return_value = True
        self.assertEqual(self.client.get(API + '/status').status_code, 403)

        self.is_demo.return_value = False
        self.owner_query.return_value.first.return_value = None
        self.assertEqual(self.client.get(API + '/status').status_code, 403)
        self.graph.assert_not_called()

    def test_demo_runtime_accepts_only_demo_owner_and_demo_sender(self):
        demo_environment = {
            'APP_RUNTIME': 'demo',
            'META_WA_PHONE_NUMBER_ID': SALON_DEMO_PHONE_NUMBER_ID,
            'META_WA_BUSINESS_ACCOUNT_ID': SALON_DEMO_WABA_ID,
        }
        self.is_demo.return_value = True
        with patch.dict(os.environ, demo_environment):
            response = self.client.get(API + '/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['runtime'], 'demo')
        self.assertTrue(response.get_json()['connected'])

        self.is_demo.return_value = False
        with patch.dict(os.environ, demo_environment):
            self.assertEqual(self.client.get(API + '/status').status_code, 403)

        self.is_demo.return_value = True
        with patch.dict(os.environ, {'APP_RUNTIME': 'demo'}):
            mismatched = self.client.get(API + '/status').get_json()
        self.assertFalse(mismatched['connected'])
        self.assertEqual(mismatched['error_code'], 'configuration_invalid')

    def test_missing_configuration_fails_closed(self):
        for variable in (*MetaWhatsAppService.REQUIRED_ENV, *MetaWhatsAppService.WEBHOOK_ENV):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: ''}):
                response = self.client.get(API + '/status')
                body = response.get_json()
                self.assertIn(variable, body['missing_configuration'])
                self.assertFalse(body['sending_enabled'])
        self.graph.assert_not_called()

    def test_other_whatsapp_accounts_are_rejected(self):
        with patch.dict(os.environ, {'META_WA_BUSINESS_ACCOUNT_ID': SALON_DEMO_WABA_ID}):
            body = self.client.get(API + '/status').get_json()
            self.assertEqual(body['error_code'], 'configuration_invalid')
        with patch.dict(os.environ, {'META_WA_PHONE_NUMBER_ID': '1234567890'}):
            body = self.client.get(API + '/status').get_json()
            self.assertEqual(body['error_code'], 'configuration_invalid')
        self.graph.assert_not_called()

    def test_production_sender_uses_supported_fields_and_waba_membership(self):
        sender = MetaWhatsAppService(production=True).get_sender()

        self.assertEqual(sender['id'], SALON_PRODUCTION_PHONE_NUMBER_ID)
        self.assertEqual(sender['phone_status'], 'CONNECTED')
        direct_call, waba_call = self.graph.call_args_list
        self.assertEqual(
            direct_call.kwargs['params']['fields'],
            'display_phone_number,verified_name,quality_rating',
        )
        self.assertNotIn('status', direct_call.kwargs['params']['fields'])
        self.assertIn(
            f'/{SALON_PRODUCTION_WABA_ID}/phone_numbers',
            waba_call.args[1],
        )
        self.assertEqual(waba_call.kwargs['params']['fields'], 'id')

    def test_production_sender_rejects_mismatched_direct_phone_id(self):
        def mismatched_sender(method, url, **kwargs):
            return FakeResponse(200, {
                'id': '9999999999999999',
                'verified_name': 'Unexpected Sender',
            })

        service = MetaWhatsAppService(
            production=True,
            request_func=mismatched_sender,
        )
        with self.assertRaises(MetaWhatsAppError) as raised:
            service.get_sender()
        self.assertEqual(raised.exception.code, 'sender_mismatch')

    def test_production_sender_fails_closed_when_phone_is_not_under_waba(self):
        def phone_not_assigned(method, url, **kwargs):
            if url.rstrip('/').endswith(f'/{SALON_PRODUCTION_PHONE_NUMBER_ID}'):
                return FakeResponse(200, {
                    'id': SALON_PRODUCTION_PHONE_NUMBER_ID,
                    'verified_name': 'Priyanka Nature Cure',
                    'display_phone_number': '+1 202 555 0110',
                    'quality_rating': 'GREEN',
                })
            if url.rstrip('/').endswith(
                f'/{SALON_PRODUCTION_WABA_ID}/phone_numbers'
            ):
                return FakeResponse(200, {'data': [{'id': '9999999999999999'}]})
            raise AssertionError('Unexpected synthetic Graph request')

        service = MetaWhatsAppService(
            production=True,
            request_func=phone_not_assigned,
        )
        with self.assertRaises(MetaWhatsAppError) as raised:
            service.get_sender()
        self.assertEqual(raised.exception.code, 'phone_waba_mismatch')

    def test_status_and_templates_are_read_only_and_sanitized(self):
        handler = ListHandler()
        self.client.application.logger.addHandler(handler)
        response = self.client.get(API + '/status')
        body = response.get_json()
        self.assertTrue(body['connected'])
        self.assertTrue(body['template_access'])
        self.assertTrue(body['waba_has_webhook_subscriptions'])
        self.assertTrue(body['billing_required'])
        self.assertFalse(body['webhook_ready'])
        self.assertFalse(body['sending_enabled'])
        self.assertFalse(body['controlled_test_enabled'])
        self.assertFalse(body['media_configured'])

        templates = self.client.get(API + '/templates?status=approved')
        self.assertEqual(templates.status_code, 200)
        self.assertEqual(templates.get_json()['templates'], [TEMPLATE])

        self.client.application.logger.removeHandler(handler)
        combined = (
            response.get_data(as_text=True)
            + templates.get_data(as_text=True)
            + '\n'.join(handler.messages)
        )
        for name in (
            'META_WA_ACCESS_TOKEN',
            'META_WA_APP_SECRET',
            'META_WA_WEBHOOK_VERIFY_TOKEN',
        ):
            self.assertNotIn(os.environ[name], combined)

    def test_controlled_send_is_disabled_before_meta_call(self):
        response = self.client.post(API + '/test-messages', json=self.controlled_payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['error_code'], 'send_disabled')
        self.graph.assert_not_called()

    def test_controlled_test_is_blocked_until_billing_is_verified(self):
        with patch.dict(os.environ, {
            'WHATSAPP_PRODUCTION_TEST_ENABLED': 'true',
            'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'false',
        }):
            response = self.client.post(
                API + '/test-messages', json=self.controlled_payload()
            )
        self.assertEqual(response.status_code, 403)
        self.assertIn('payment method', response.get_json()['error'].lower())

    def test_controlled_test_rejects_non_allowlisted_and_non_opted_in_recipients(self):
        enabled = {
            'WHATSAPP_PRODUCTION_BILLING_VERIFIED': 'true',
            'WHATSAPP_PRODUCTION_TEST_ENABLED': 'true',
            'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'false',
        }
        with patch.dict(os.environ, enabled):
            unknown = self.client.post(
                API + '/test-messages', json=self.controlled_payload('not-allowlisted')
            )
        self.assertEqual(unknown.status_code, 403)

        without_opt_in = json.dumps([{
            'id': 'owner-test',
            'label': 'Owner test',
            'phone': '+12025550110',
            'opted_in': False,
        }])
        with patch.dict(os.environ, {
            **enabled,
            'META_WA_TEST_RECIPIENTS_JSON': without_opt_in,
        }):
            not_opted_in = self.client.post(
                API + '/test-messages', json=self.controlled_payload()
            )
        self.assertEqual(not_opted_in.status_code, 503)
        self.assertNotIn('+12025550110', not_opted_in.get_data(as_text=True))

    def test_controlled_test_can_send_before_webhook_verification(self):
        message = self.pending_message()
        event_query = MagicMock()
        event_query.order_by.return_value = []
        with patch.dict(os.environ, {
            'WHATSAPP_PRODUCTION_BILLING_VERIFIED': 'true',
            'WHATSAPP_PRODUCTION_TEST_ENABLED': 'true',
            'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'false',
            'WHATSAPP_PRODUCTION_SEND_ENABLED': 'false',
        }), patch.object(
            routes, '_reserve_message', return_value=(message, True),
        ), patch.object(
            routes, '_enforce_send_rate_limits',
        ) as rate_limit, patch.object(
            routes.WhatsAppWebhookEvent, 'objects', return_value=event_query,
        ):
            response = self.client.post(
                API + '/test-messages', json=self.controlled_payload()
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()['message']['status'], 'accepted')
        rate_limit.assert_called_once_with(OWNER_ID, production=True)
        self.assertFalse(response.get_json()['duplicate'])

    def test_controlled_test_does_not_enable_customer_sending(self):
        with patch.dict(os.environ, {
            'WHATSAPP_PRODUCTION_BILLING_VERIFIED': 'true',
            'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'true',
            'WHATSAPP_PRODUCTION_TEST_ENABLED': 'true',
            'WHATSAPP_PRODUCTION_SEND_ENABLED': 'false',
        }):
            body = self.client.get(API + '/status').get_json()
        self.assertTrue(body['controlled_test_enabled'])
        self.assertFalse(body['sending_enabled'])
        self.assertFalse(body['bulk_campaigns_enabled'])

        customer_response = self.client.post(API + '/messages', json={
            'request_id': '00000000-0000-4000-8000-000000000002',
            'customer_id': '000000000000000000000099',
            'template_name': TEMPLATE['name'],
            'language': TEMPLATE['language'],
        })
        self.assertEqual(customer_response.status_code, 403)
        self.assertEqual(customer_response.get_json()['error_code'], 'send_disabled')

    def test_webhook_verification_contract(self):
        wrong = self.client.get(API + '/webhook', query_string={
            'hub.mode': 'subscribe',
            'hub.verify_token': 'wrong',
            'hub.challenge': 'challenge',
        })
        self.assertEqual(wrong.status_code, 403)

        valid = self.client.get(API + '/webhook', query_string={
            'hub.mode': 'subscribe',
            'hub.verify_token': ENV['META_WA_WEBHOOK_VERIFY_TOKEN'],
            'hub.challenge': 'challenge',
        })
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.get_data(as_text=True), 'challenge')
        self.graph.assert_not_called()

    def test_webhook_requires_valid_hmac_and_matching_account(self):
        payload = {
            'object': 'whatsapp_business_account',
            'entry': [{
                'id': SALON_PRODUCTION_WABA_ID,
                'changes': [{
                    'field': 'messages',
                    'value': {
                        'messaging_product': 'whatsapp',
                        'metadata': {'phone_number_id': SALON_PRODUCTION_PHONE_NUMBER_ID},
                        'statuses': [{
                            'id': 'wamid.synthetic',
                            'status': 'delivered',
                            'timestamp': '123',
                        }],
                    },
                }],
            }],
        }
        raw = json.dumps(payload, separators=(',', ':')).encode()
        signature = 'sha256=' + hmac.new(
            SYNTHETIC_SECRET.encode(),
            raw,
            hashlib.sha256,
        ).hexdigest()
        handler = ListHandler()
        self.client.application.logger.addHandler(handler)

        with patch.object(routes, 'WhatsAppWebhookEvent') as event_model, patch.object(
            routes,
            '_update_message_status',
        ) as update_status, patch.object(
            routes,
            'update_campaign_recipient_status',
        ) as update_campaign_status, patch.object(
            routes,
            'update_invoice_notification_status',
        ) as update_invoice_status:
            missing = self.client.post(
                API + '/webhook',
                data=raw,
                content_type='application/json',
            )
            self.assertEqual(missing.status_code, 401)
            event_model.assert_not_called()

            malformed = self.client.post(
                API + '/webhook',
                data=raw,
                content_type='application/json',
                headers={
                    'X-Hub-Signature-256': 'sha256= not-a-signature',
                    'Content-Encoding': 'identity',
                },
            )
            self.assertEqual(malformed.status_code, 401)
            event_model.assert_not_called()

            invalid = self.client.post(
                API + '/webhook',
                data=raw,
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=' + ('0' * 64)},
            )
            self.assertEqual(invalid.status_code, 401)
            event_model.assert_not_called()

            altered = self.client.post(
                API + '/webhook',
                data=raw + b'\n',
                content_type='application/json',
                headers={'X-Hub-Signature-256': signature},
            )
            self.assertEqual(altered.status_code, 401)
            event_model.assert_not_called()

            valid = self.client.post(
                API + '/webhook',
                data=raw,
                content_type='application/json',
                headers={'X-Hub-Signature-256': signature},
            )
            self.assertEqual(valid.status_code, 200)
            self.assertEqual(valid.get_json()['processed'], 1)
            event_model.return_value.save.assert_called_once_with(force_insert=True)
            update_status.assert_called_once()
            update_campaign_status.assert_called_once_with(
                'wamid.synthetic',
                'delivered',
                '',
                account={
                    'waba_id': SALON_PRODUCTION_WABA_ID,
                    'phone_number_id': SALON_PRODUCTION_PHONE_NUMBER_ID,
                },
            )
            update_invoice_status.assert_called_once_with(
                'wamid.synthetic',
                'delivered',
                '',
                account={
                    'waba_id': SALON_PRODUCTION_WABA_ID,
                    'phone_number_id': SALON_PRODUCTION_PHONE_NUMBER_ID,
                },
            )

        self.client.application.logger.removeHandler(handler)
        records = [json.loads(message) for message in handler.messages]
        self.assertEqual(len(records), 4)
        expected_keys = {
            'event',
            'signature_header_present',
            'signature_header_format_valid',
            'raw_body_byte_length',
            'app_secret_length',
            'app_secret_sha256_prefix',
            'raw_body_sha256_prefix',
            'supplied_signature_prefix',
            'calculated_signature_prefix',
            'Content-Type',
            'app_secret_configured',
            'APP_RUNTIME',
            'VERCEL_ENV',
        }
        self.assertEqual(set(records[0]), expected_keys)
        self.assertFalse(records[0]['signature_header_present'])
        self.assertFalse(records[0]['signature_header_format_valid'])
        self.assertTrue(records[1]['signature_header_present'])
        self.assertFalse(records[1]['signature_header_format_valid'])
        self.assertEqual(records[1]['Content-Encoding'], 'identity')
        self.assertTrue(records[2]['signature_header_present'])
        self.assertTrue(records[2]['signature_header_format_valid'])
        self.assertEqual(records[2]['raw_body_byte_length'], len(raw))
        self.assertTrue(records[3]['signature_header_format_valid'])
        self.assertEqual(records[3]['raw_body_byte_length'], len(raw) + 1)
        secret_sha256 = hashlib.sha256(SYNTHETIC_SECRET.encode()).hexdigest()
        calculated_signature = hmac.new(
            SYNTHETIC_SECRET.encode(), raw, hashlib.sha256
        ).hexdigest()
        altered_signature = hmac.new(
            SYNTHETIC_SECRET.encode(), raw + b'\n', hashlib.sha256
        ).hexdigest()
        for record in records:
            self.assertEqual(record['app_secret_length'], len(SYNTHETIC_SECRET))
            self.assertEqual(record['app_secret_sha256_prefix'], secret_sha256[:12])
            for field in (
                'app_secret_sha256_prefix',
                'raw_body_sha256_prefix',
                'calculated_signature_prefix',
            ):
                self.assertRegex(record[field], r'^[0-9a-f]{12}$')
        self.assertIsNone(records[0]['supplied_signature_prefix'])
        self.assertIsNone(records[1]['supplied_signature_prefix'])
        self.assertEqual(records[2]['supplied_signature_prefix'], '0' * 12)
        self.assertEqual(records[3]['supplied_signature_prefix'], signature[7:19])
        self.assertEqual(
            [record['raw_body_sha256_prefix'] for record in records[:3]],
            [hashlib.sha256(raw).hexdigest()[:12]] * 3,
        )
        self.assertEqual(
            records[3]['raw_body_sha256_prefix'],
            hashlib.sha256(raw + b'\n').hexdigest()[:12],
        )
        self.assertEqual(records[2]['calculated_signature_prefix'], calculated_signature[:12])
        self.assertEqual(records[3]['calculated_signature_prefix'], altered_signature[:12])
        diagnostics = '\n'.join(handler.messages)
        for forbidden in (
            SYNTHETIC_SECRET,
            signature,
            raw.decode('utf-8'),
            secret_sha256,
            calculated_signature,
            altered_signature,
            'sha256=',
            SALON_PRODUCTION_WABA_ID,
            SALON_PRODUCTION_PHONE_NUMBER_ID,
            'wamid.synthetic',
        ):
            self.assertNotIn(forbidden, diagnostics)


if __name__ == '__main__':
    unittest.main(verbosity=2)
