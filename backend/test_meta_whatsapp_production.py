"""Production WhatsApp integration contract tests with mocked external I/O."""
import hashlib
import hmac
import json
import os
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask
from PIL import Image, PngImagePlugin
from werkzeug.datastructures import FileStorage

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
    MetaWhatsAppService,
    SALON_DEMO_WABA_ID,
    SALON_PRODUCTION_PHONE_NUMBER_ID,
    SALON_PRODUCTION_WABA_ID,
)


OWNER_ID = '000000000000000000000001'
API = '/api/integrations/whatsapp'
SYNTHETIC_SECRET = 'synthetic-production-app-secret'
ENV = {
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
        if resource == SALON_PRODUCTION_PHONE_NUMBER_ID:
            return FakeResponse(200, {
                'id': resource,
                'verified_name': 'Priyanka Nature Cure',
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
        if resource == 'subscribed_apps':
            return FakeResponse(200, {'data': [{'id': 'synthetic-app'}]})
        raise AssertionError(f'Unexpected mocked Meta resource: {resource}')

    def test_owner_authentication_is_required(self):
        self.current_user.return_value = None
        self.assertEqual(self.client.get(API + '/status').status_code, 401)

        self.current_user.return_value = {'role': 'manager', 'user_id': OWNER_ID}
        self.assertEqual(self.client.get(API + '/status').status_code, 403)
        self.graph.assert_not_called()

    def test_active_production_owner_is_required(self):
        self.is_demo.return_value = True
        self.assertEqual(self.client.get(API + '/status').status_code, 403)

        self.is_demo.return_value = False
        self.owner_query.return_value.first.return_value = None
        self.assertEqual(self.client.get(API + '/status').status_code, 403)
        self.graph.assert_not_called()

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

    def test_status_and_templates_are_read_only_and_sanitized(self):
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

        combined = response.get_data(as_text=True) + templates.get_data(as_text=True)
        for name in ('META_WA_ACCESS_TOKEN', 'META_WA_APP_SECRET', 'META_WA_WEBHOOK_VERIFY_TOKEN'):
            self.assertNotIn(os.environ[name], combined)

    def test_controlled_send_is_disabled_before_meta_call(self):
        payload = {
            'request_id': '00000000-0000-4000-8000-000000000001',
            'recipient_id': 'owner-test',
            'template_name': TEMPLATE['name'],
            'language': TEMPLATE['language'],
        }
        response = self.client.post(API + '/test-messages', json=payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['error_code'], 'send_disabled')
        self.graph.assert_not_called()

    def test_controlled_test_stays_blocked_until_webhook_is_verified(self):
        with patch.dict(os.environ, {
            'WHATSAPP_PRODUCTION_BILLING_VERIFIED': 'true',
            'WHATSAPP_PRODUCTION_TEST_ENABLED': 'true',
            'WHATSAPP_PRODUCTION_WEBHOOK_VERIFIED': 'false',
        }):
            body = self.client.get(API + '/status').get_json()
        self.assertFalse(body['controlled_test_enabled'])
        self.assertFalse(body['sending_enabled'])
        self.assertIn('webhook', body['send_disabled_reason'].lower())

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

        with patch.object(routes, 'WhatsAppWebhookEvent') as event_model, patch.object(
            routes,
            '_update_message_status',
        ) as update_status:
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
                headers={'X-Hub-Signature-256': 'sha256= not-a-signature'},
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
