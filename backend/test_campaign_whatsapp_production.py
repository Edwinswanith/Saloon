"""Durable production WhatsApp campaign tests with no external I/O."""
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'synthetic-campaign-test-jwt-secret')

from routes import campaign_routes as routes
from utils import campaign_whatsapp as campaign_wa
from utils.meta_whatsapp_service import MetaWhatsAppError


REQUEST_ID = '00000000-0000-4000-8000-000000000020'
MEDIA_ID = '000000000000000000000099'
OWNER = {'role': 'owner', 'user_id': '000000000000000000000001', 'name': 'Owner'}
BASE_ENV = {
    'APP_RUNTIME': 'production',
    'WHATSAPP_PRODUCTION_SEND_ENABLED': 'true',
    'WHATSAPP_CAMPAIGN_SEND_ENABLED': 'true',
    'WHATSAPP_CAMPAIGN_BATCH_SIZE': '20',
    'WHATSAPP_CAMPAIGN_WORKER_SECRET': 's' * 32,
}
IMAGE_TEMPLATE = {
    'name': campaign_wa.CAMPAIGN_TEMPLATE_NAME,
    'language': campaign_wa.CAMPAIGN_TEMPLATE_LANGUAGE,
    'status': 'APPROVED',
    'category': 'MARKETING',
    'components': [
        {'type': 'HEADER', 'format': 'IMAGE'},
        {'type': 'BODY', 'text': 'Priyanka promotional offer'},
    ],
}


class FakeDocument:
    def update(self, **operations):
        for operation, value in operations.items():
            if operation.startswith('set__'):
                setattr(self, operation[5:], value)
            elif operation.startswith('unset__'):
                setattr(self, operation[7:], None)

    def reload(self):
        return self


class FakeCampaign(FakeDocument):
    def __init__(self, eligible_count=0):
        self.id = '000000000000000000000050'
        self.branch = None
        self.media_asset = SimpleNamespace(id=MEDIA_ID)
        self.meta_media_id = None
        self.created_by_id = OWNER['user_id']
        self.requested_count = eligible_count
        self.eligible_count = eligible_count
        self.excluded_count = 0
        self.excluded_no_consent = 0
        self.excluded_invalid_phone = 0
        self.excluded_not_found = 0
        self.queued_count = eligible_count
        self.processing_count = 0
        self.accepted_count = 0
        self.sent_count = 0
        self.delivered_count = 0
        self.read_count = 0
        self.failed_count = 0
        self.unknown_count = 0
        self.duplicate_count = 0
        self.pause_code = None
        self.pause_reason = None
        self.status = 'queued'


class FakeRecipient(FakeDocument):
    def __init__(self, index, campaign=None):
        self.id = f'{index + 1000:024x}'
        self.normalized_recipient = f'91987654{index:04d}'
        self.campaign = campaign
        self.status = 'queued'
        self.meta_message_id = None
        self.error_code = None
        self.error_message = None


def customer(index, *, consent=True, mobile=None):
    return SimpleNamespace(
        id=f'{index:024x}',
        mobile=mobile or f'98765{index:05d}',
        whatsapp_consent=consent,
        branch=None,
    )


def payload(customer_ids, **overrides):
    value = {
        'request_id': REQUEST_ID,
        'message_text': 'Internal CRM campaign description',
        'customer_ids': customer_ids,
        'delivery_method': 'api',
        'template_name': campaign_wa.CAMPAIGN_TEMPLATE_NAME,
        'language': campaign_wa.CAMPAIGN_TEMPLATE_LANGUAGE,
        'media_asset_id': MEDIA_ID,
    }
    value.update(overrides)
    return value


class CampaignCreationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def configured_service(self):
        service = MagicMock()
        service.assert_configured = MagicMock()
        service.access_token = 'synthetic-campaign-access-token'
        service.business_account_id = '4800759546811980'
        service.phone_number_id = '1521113507744203'
        service.get_sender.return_value = {'phone_status': 'CONNECTED'}
        service.get_templates.return_value = [IMAGE_TEMPLATE]
        return service

    def call(self, data, customers, *, env=None):
        with patch.dict(os.environ, env or BASE_ENV, clear=True), self.app.test_request_context(
            '/api/campaigns/send',
            method='POST',
            json=data,
            headers={'Idempotency-Key': data.get('request_id', '')},
        ), patch.object(routes, 'is_demo_branch', return_value=False):
            response, status = routes._send_meta_campaign(
                data, OWNER, None, 'all', customers, data.get('customer_ids', [])
            )
            return response.get_json(), status

    def test_campaign_is_disabled_by_default_and_requires_both_flags(self):
        item = customer(1)
        body, status = self.call(
            payload([str(item.id)]), [item], env={'APP_RUNTIME': 'production'}
        )
        self.assertEqual((status, body['error_code']), (403, 'send_disabled'))
        body, status = self.call(
            payload([str(item.id)]),
            [item],
            env={'APP_RUNTIME': 'production', 'WHATSAPP_PRODUCTION_SEND_ENABLED': 'true'},
        )
        self.assertEqual((status, body['error_code']), (403, 'campaign_disabled'))

    def test_demo_runtime_cannot_queue_production_campaign(self):
        item = customer(1)
        with patch.object(routes, 'MetaWhatsAppService') as service:
            body, status = self.call(
                payload([str(item.id)]), [item], env={**BASE_ENV, 'APP_RUNTIME': 'demo'}
            )
        self.assertEqual((status, body['error_code']), (403, 'production_runtime_required'))
        service.assert_not_called()

    def test_consent_and_phone_validation_are_server_side(self):
        valid = customer(1, mobile='+91 98765 43210')
        no_consent = customer(2, consent=False)
        invalid = customer(3, mobile='12345')
        eligible, excluded = routes._classify_campaign_customers(
            [valid, no_consent, invalid],
            [str(valid.id), str(no_consent.id), str(invalid.id), 'f' * 24],
        )
        self.assertEqual(eligible, [(valid, '919876543210')])
        self.assertEqual(excluded, {
            'excluded_not_found': 1,
            'excluded_no_consent': 1,
            'excluded_invalid_phone': 1,
        })

    def test_150_selected_queues_137_and_starts_first_batch(self):
        customers = [customer(index + 1) for index in range(150)]
        for item in customers[:8]:
            item.whatsapp_consent = False
        for item in customers[8:13]:
            item.mobile = 'invalid'
        ids = [str(item.id) for item in customers]
        campaign = FakeCampaign(137)
        campaign.requested_count = 150
        campaign.excluded_count = 13
        campaign.excluded_no_consent = 8
        campaign.excluded_invalid_phone = 5
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')

        def refresh(record):
            record.queued_count = 137
            record.status = 'queued'
            return record

        def process_first_batch(campaign_id):
            self.assertEqual(campaign_id, str(campaign.id))
            campaign.queued_count = 117
            campaign.accepted_count = 20
            campaign.status = 'queued'
            return {
                'processed': True,
                'campaign': routes._campaign_summary(campaign),
                'batch_size': 20,
                'claimed_count': 20,
                'accepted_in_batch': 20,
                'failed_in_batch': 0,
                'unknown_in_batch': 0,
                'paused': False,
                'deferred': False,
            }

        with patch.object(routes, 'MetaWhatsAppService', return_value=service), patch.object(
            routes, '_media_scope', return_value=('production:4800759546811980', None, OWNER['user_id'])
        ), patch.object(
            routes, '_find_scoped_media_asset', return_value=media
        ), patch.object(
            routes, '_load_or_create_campaign', return_value=(campaign, True, None)
        ), patch.object(
            routes, 'reserve_campaign_recipients', return_value={
                'created_count': 137, 'duplicate_count': 0,
            }
        ) as reserve, patch.object(
            routes, 'refresh_campaign_aggregates', side_effect=refresh
        ), patch.object(
            routes, '_process_campaign_batch', side_effect=process_first_batch
        ) as process_batch, patch.object(routes, '_read_stored_image') as read_image:
            body, status = self.call(payload(ids), customers)

        self.assertEqual(status, 202)
        self.assertEqual(
            (body['requested_count'], body['eligible_count'], body['excluded_count'], body['queued_count']),
            (150, 137, 13, 117),
        )
        self.assertEqual(body['accepted_count'], 20)
        self.assertEqual(body['first_batch']['claimed_count'], 20)
        reserve.assert_called_once()
        process_batch.assert_called_once_with(str(campaign.id))
        service.upload_image.assert_not_called()
        service.send_template.assert_not_called()
        read_image.assert_not_called()
        self.assertFalse(hasattr(routes, 'send_whatsapp_message'))

    def test_1200_recipient_campaign_creation_has_no_recipient_ceiling(self):
        customers = [customer(index + 1) for index in range(1200)]
        ids = [str(item.id) for item in customers]
        campaign = FakeCampaign(1200)
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')

        def refresh(record):
            record.queued_count = 1200
            record.status = 'queued'
            return record

        first_batch = {
            'processed': True,
            'campaign': {
                **routes._campaign_summary(campaign),
                'queued_count': 1180,
                'accepted_count': 20,
                'status': 'queued',
            },
            'batch_size': 20,
            'claimed_count': 20,
            'accepted_in_batch': 20,
            'paused': False,
            'deferred': False,
        }

        with patch.object(routes, 'MetaWhatsAppService', return_value=service), patch.object(
            routes, '_media_scope', return_value=('production:4800759546811980', None, OWNER['user_id'])
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_load_or_create_campaign', return_value=(campaign, True, None)
        ), patch.object(
            routes, 'reserve_campaign_recipients', return_value={
                'created_count': 1200, 'duplicate_count': 0,
            }
        ) as reserve, patch.object(
            routes, 'refresh_campaign_aggregates', side_effect=refresh
        ), patch.object(
            routes, '_process_campaign_batch', return_value=first_batch
        ):
            body, status = self.call(payload(ids), customers)

        self.assertEqual(status, 202)
        self.assertEqual(body['requested_count'], 1200)
        self.assertEqual(body['eligible_count'], 1200)
        self.assertEqual(body['queued_count'], 1180)
        self.assertEqual(body['first_batch']['claimed_count'], 20)
        reserve.assert_called_once()
        service.send_template.assert_not_called()

    def test_creation_has_no_recipient_ceiling(self):
        with patch.dict(os.environ, {'WHATSAPP_CAMPAIGN_BATCH_SIZE': '20'}, clear=True):
            self.assertEqual(campaign_wa.campaign_batch_size(), 20)

    def test_template_and_private_media_are_required(self):
        item = customer(1)
        with patch.object(routes, 'MetaWhatsAppService') as service:
            body, status = self.call(
                payload([str(item.id)], template_name='another_template'), [item]
            )
        self.assertEqual((status, body['error_code']), (422, 'campaign_template_not_allowed'))
        service.assert_not_called()
        body, status = self.call(payload([str(item.id)], media_asset_id=''), [item])
        self.assertEqual((status, body['error_code']), (422, 'campaign_media_required'))

    def test_approved_marketing_template_is_checked_before_queueing(self):
        item = customer(1)
        service = self.configured_service()
        service.get_templates.return_value = [{**IMAGE_TEMPLATE, 'category': 'UTILITY'}]
        with patch.object(routes, 'MetaWhatsAppService', return_value=service):
            body, status = self.call(payload([str(item.id)]), [item])
        self.assertEqual((status, body['error_code']), (422, 'campaign_template_unavailable'))

    def test_retry_reserves_idempotently_but_never_sends(self):
        item = customer(1)
        campaign = FakeCampaign(1)
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID)
        with patch.object(routes, 'MetaWhatsAppService', return_value=service), patch.object(
            routes, '_media_scope', return_value=('production:4800759546811980', None, OWNER['user_id'])
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_load_or_create_campaign', return_value=(campaign, False, None)
        ), patch.object(
            routes, 'reserve_campaign_recipients', return_value={
                'created_count': 0, 'duplicate_count': 1,
            }
        ) as reserve, patch.object(
            routes, 'refresh_campaign_aggregates', return_value=campaign
        ), patch.object(routes, '_process_campaign_batch') as process_batch:
            body, status = self.call(payload([str(item.id)]), [item])
        self.assertEqual(status, 200)
        self.assertTrue(body['duplicate'])
        reserve.assert_called_once()
        process_batch.assert_not_called()
        service.send_template.assert_not_called()

    def test_meta_error_text_cannot_leak_access_token(self):
        service = SimpleNamespace(access_token='secret-token-value')
        safe = routes._safe_campaign_error(
            MetaWhatsAppError('Bearer secret-token-value was rejected.'), service
        )
        self.assertNotIn('secret-token-value', safe)


class QueuePersistenceTests(unittest.TestCase):
    def test_large_audience_is_persisted_in_internal_chunks(self):
        campaign = FakeCampaign(1201)
        media = SimpleNamespace(id=MEDIA_ID)
        eligible = [(customer(index + 1), '919876543210') for index in range(1201)]
        collection = MagicMock()

        def bulk_write(operations, ordered=False):
            self.assertFalse(ordered)
            return SimpleNamespace(upserted_count=len(operations))

        collection.bulk_write.side_effect = bulk_write
        with patch.object(
            campaign_wa.CampaignWhatsAppRecipient,
            '_get_collection',
            return_value=collection,
        ):
            result = campaign_wa.reserve_campaign_recipients(
                campaign,
                eligible,
                media,
                {'waba_id': 'waba', 'phone_number_id': 'phone'},
            )
        self.assertEqual(result, {'created_count': 1201, 'duplicate_count': 0})
        self.assertEqual(collection.bulk_write.call_count, 3)
        self.assertEqual(
            [len(call.args[0]) for call in collection.bulk_write.call_args_list],
            [500, 500, 201],
        )

    def test_worker_claim_query_can_never_reclaim_accepted_recipient(self):
        campaign = FakeCampaign(1)
        collection = MagicMock()
        collection.find_one_and_update.return_value = None
        with patch.object(
            campaign_wa.CampaignWhatsAppRecipient,
            '_get_collection',
            return_value=collection,
        ):
            self.assertIsNone(campaign_wa.claim_queued_recipient(campaign, 'worker-id'))
        claim_filter = collection.find_one_and_update.call_args.args[0]
        self.assertEqual(claim_filter['status'], 'queued')
        self.assertNotIn('accepted', claim_filter.values())


class CampaignWorkerTests(unittest.TestCase):
    def configured_service(self):
        service = MagicMock()
        service.assert_configured = MagicMock()
        service.access_token = 'synthetic-campaign-access-token'
        service.business_account_id = '4800759546811980'
        service.phone_number_id = '1521113507744203'
        service.get_sender.return_value = {'phone_status': 'CONNECTED'}
        service.get_templates.return_value = [IMAGE_TEMPLATE]
        service.upload_image.return_value = '1234567890'
        service.send_template.side_effect = lambda *args, **kwargs: {
            'message_id': f'wamid.{args[0]}', 'status': 'accepted'
        }
        return service

    def test_worker_authentication_is_fail_closed(self):
        app = Flask(__name__)
        with patch.dict(os.environ, BASE_ENV, clear=True):
            with app.test_request_context('/process', method='POST'):
                self.assertFalse(routes._campaign_worker_authorized())
            with app.test_request_context(
                '/process', method='POST', headers={'Authorization': 'Bearer wrong'}
            ):
                self.assertFalse(routes._campaign_worker_authorized())
            with app.test_request_context(
                '/process', method='POST',
                headers={'Authorization': f"Bearer {BASE_ENV['WHATSAPP_CAMPAIGN_WORKER_SECRET']}"},
            ):
                self.assertTrue(routes._campaign_worker_authorized())

    def test_worker_endpoint_rejects_missing_and_incorrect_secret(self):
        app = Flask(__name__)
        app.register_blueprint(routes.campaign_bp, url_prefix='/api/campaigns')
        client = app.test_client()
        with patch.dict(os.environ, BASE_ENV, clear=True):
            missing = client.post('/api/campaigns/process-queue', json={})
            incorrect = client.post(
                '/api/campaigns/process-queue',
                json={},
                headers={'Authorization': 'Bearer incorrect-worker-secret'},
            )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(incorrect.status_code, 401)
        self.assertEqual(missing.get_json(), {'error': 'Authentication required'})
        self.assertEqual(incorrect.get_json(), {'error': 'Authentication required'})

    def test_authenticated_crm_user_can_process_only_an_accessible_campaign(self):
        app = Flask(__name__)
        app.register_blueprint(routes.campaign_bp, url_prefix='/api/campaigns')
        client = app.test_client()
        no_work = {
            'processed': False,
            'batch_size': 20,
            'claimed_count': 0,
        }
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'get_current_user', return_value=OWNER
        ), patch.object(
            routes, '_crm_user_can_process_campaign', return_value=True
        ) as can_process, patch.object(
            routes, '_process_campaign_batch', return_value=no_work
        ) as process_batch:
            response = client.post(
                '/api/campaigns/process-queue',
                json={'campaign_id': '000000000000000000000050'},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), no_work)
        can_process.assert_called_once_with('000000000000000000000050', OWNER)
        process_batch.assert_called_once_with('000000000000000000000050')

    def test_crm_worker_rejects_staff_missing_id_and_inaccessible_campaign(self):
        app = Flask(__name__)
        app.register_blueprint(routes.campaign_bp, url_prefix='/api/campaigns')
        client = app.test_client()
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'get_current_user', return_value={'role': 'staff', 'user_id': '1'}
        ):
            staff = client.post(
                '/api/campaigns/process-queue',
                json={'campaign_id': '000000000000000000000050'},
            )
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'get_current_user', return_value=OWNER
        ):
            missing_id = client.post('/api/campaigns/process-queue', json={})
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'get_current_user', return_value=OWNER
        ), patch.object(
            routes, '_crm_user_can_process_campaign', return_value=False
        ), patch.object(routes, '_process_campaign_batch') as process_batch:
            inaccessible = client.post(
                '/api/campaigns/process-queue',
                json={'campaign_id': '000000000000000000000050'},
            )
        self.assertEqual(staff.status_code, 403)
        self.assertEqual(missing_id.status_code, 400)
        self.assertEqual(inaccessible.status_code, 404)
        process_batch.assert_not_called()

    def test_authenticated_worker_respects_runtime_and_send_flags(self):
        app = Flask(__name__)
        app.register_blueprint(routes.campaign_bp, url_prefix='/api/campaigns')
        client = app.test_client()
        cases = [
            ({**BASE_ENV, 'APP_RUNTIME': 'demo'}, 403, 'production_runtime_required'),
            ({**BASE_ENV, 'WHATSAPP_PRODUCTION_SEND_ENABLED': 'false'}, 403, 'send_disabled'),
            ({**BASE_ENV, 'WHATSAPP_CAMPAIGN_SEND_ENABLED': 'false'}, 403, 'campaign_disabled'),
        ]
        for env, status, error_code in cases:
            with self.subTest(error_code=error_code), patch.dict(
                os.environ, env, clear=True
            ), patch.object(
                routes, 'get_current_user', return_value=OWNER
            ), patch.object(routes, '_process_campaign_batch') as process_batch:
                response = client.post(
                    '/api/campaigns/process-queue',
                    json={'campaign_id': '000000000000000000000050'},
                )
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.get_json()['error_code'], error_code)
            process_batch.assert_not_called()

    def test_worker_processes_only_configured_batch_and_reuses_media(self):
        campaign = FakeCampaign(137)
        recipients = [FakeRecipient(index, campaign) for index in range(20)]
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')

        def refresh(record):
            record.accepted_count = sum(item.status == 'accepted' for item in recipients)
            record.queued_count = 137 - record.accepted_count
            record.status = 'queued' if record.queued_count else 'in_progress'
            return record

        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'claim_campaign', return_value=campaign
        ), patch.object(routes, 'expire_ambiguous_recipient_claims', return_value=0), patch.object(
            routes, 'MetaWhatsAppService', return_value=service
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_read_stored_image', return_value=b'synthetic-image'
        ), patch.object(
            routes, 'claim_queued_recipient', side_effect=recipients
        ) as claim, patch.object(routes, '_enforce_send_rate_limits'), patch.object(
            routes, 'WhatsAppWebhookEvent'
        ) as webhook, patch.object(
            routes, 'refresh_campaign_aggregates', side_effect=refresh
        ), patch.object(routes, 'release_campaign_lease') as release:
            webhook.objects.return_value.order_by.return_value = []
            result = routes._process_campaign_batch()

        self.assertEqual(result['claimed_count'], 20)
        self.assertEqual(result['accepted_in_batch'], 20)
        self.assertEqual(claim.call_count, 20)
        self.assertEqual(service.send_template.call_count, 20)
        service.upload_image.assert_called_once_with(b'synthetic-image', 'image/jpeg')
        self.assertEqual(campaign.meta_media_id, '1234567890')
        release.assert_called_once_with(campaign)

    def test_one_start_and_authenticated_batches_drain_150_without_duplicates(self):
        campaign = FakeCampaign(150)
        recipients = [FakeRecipient(index, campaign) for index in range(150)]
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')
        app = Flask(__name__)
        app.register_blueprint(routes.campaign_bp, url_prefix='/api/campaigns')
        client = app.test_client()

        def claim_campaign(_worker_id, _campaign_id=None):
            return campaign if any(item.status == 'queued' for item in recipients) else None

        def claim_recipient(_campaign, _worker_id):
            return next((item for item in recipients if item.status == 'queued'), None)

        def refresh(record):
            record.queued_count = sum(item.status == 'queued' for item in recipients)
            record.processing_count = sum(item.status == 'processing' for item in recipients)
            record.accepted_count = sum(item.status == 'accepted' for item in recipients)
            record.status = 'queued' if record.queued_count else 'in_progress'
            return record

        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'claim_campaign', side_effect=claim_campaign
        ), patch.object(routes, 'expire_ambiguous_recipient_claims', return_value=0), patch.object(
            routes, 'MetaWhatsAppService', return_value=service
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_read_stored_image', return_value=b'synthetic-image'
        ), patch.object(
            routes, 'claim_queued_recipient', side_effect=claim_recipient
        ), patch.object(routes, '_enforce_send_rate_limits'), patch.object(
            routes, 'WhatsAppWebhookEvent'
        ) as webhook, patch.object(
            routes, 'refresh_campaign_aggregates', side_effect=refresh
        ), patch.object(routes, 'release_campaign_lease'), patch.object(
            routes, 'get_current_user', return_value=OWNER
        ), patch.object(
            routes, '_crm_user_can_process_campaign', return_value=True
        ):
            webhook.objects.return_value.order_by.return_value = []
            first_batch = routes._process_campaign_batch(str(campaign.id))
            responses = [
                client.post(
                    '/api/campaigns/process-queue',
                    json={'campaign_id': str(campaign.id)},
                )
                for _index in range(7)
            ]
            results = [first_batch, *(response.get_json() for response in responses)]

        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertEqual(
            [result['claimed_count'] for result in results],
            [20, 20, 20, 20, 20, 20, 20, 10],
        )
        self.assertEqual(
            [result['accepted_in_batch'] for result in results],
            [20, 20, 20, 20, 20, 20, 20, 10],
        )
        self.assertTrue(all(item.status == 'accepted' for item in recipients))
        self.assertEqual(service.send_template.call_count, 150)
        self.assertEqual(len({item.meta_message_id for item in recipients}), 150)
        service.upload_image.assert_called_once()

    def test_local_rate_limit_requeues_and_defers_without_manual_pause(self):
        campaign = FakeCampaign(2)
        recipient = FakeRecipient(1, campaign)
        service = self.configured_service()
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'claim_campaign', return_value=campaign
        ), patch.object(routes, 'expire_ambiguous_recipient_claims', return_value=0), patch.object(
            routes, 'MetaWhatsAppService', return_value=service
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_read_stored_image', return_value=b'image'
        ), patch.object(
            routes, 'claim_queued_recipient', return_value=recipient
        ) as claim, patch.object(
            routes, '_enforce_send_rate_limits',
            side_effect=MetaWhatsAppError('Rate limited.', http_status=429, code='rate_limited'),
        ), patch.object(
            routes, 'refresh_campaign_aggregates', return_value=campaign
        ), patch.object(routes, 'release_campaign_lease') as release:
            result = routes._process_campaign_batch()
        self.assertFalse(result['paused'])
        self.assertTrue(result['deferred'])
        self.assertEqual(recipient.status, 'queued')
        self.assertEqual(claim.call_count, 1)
        service.send_template.assert_not_called()
        release.assert_called_once_with(campaign)

    def test_network_uncertainty_is_not_requeued(self):
        campaign = FakeCampaign(1)
        recipient = FakeRecipient(1, campaign)
        service = self.configured_service()
        service.send_template.side_effect = MetaWhatsAppError(
            'Meta could not be reached.', code='network_error'
        )
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'claim_campaign', return_value=campaign
        ), patch.object(routes, 'expire_ambiguous_recipient_claims', return_value=0), patch.object(
            routes, 'MetaWhatsAppService', return_value=service
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_read_stored_image', return_value=b'image'
        ), patch.object(routes, 'claim_queued_recipient', return_value=recipient), patch.object(
            routes, '_enforce_send_rate_limits'
        ), patch.object(routes, 'refresh_campaign_aggregates', return_value=campaign):
            result = routes._process_campaign_batch()
        self.assertTrue(result['paused'])
        self.assertEqual(recipient.status, 'unknown')
        self.assertEqual(result['unknown_in_batch'], 1)

    def test_meta_billing_error_requeues_recipient_and_pauses_campaign(self):
        campaign = FakeCampaign(1)
        recipient = FakeRecipient(1, campaign)
        service = self.configured_service()
        service.send_template.side_effect = MetaWhatsAppError(
            'Meta rejected the request.', code='131042'
        )
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')
        with patch.dict(os.environ, BASE_ENV, clear=True), patch.object(
            routes, 'claim_campaign', return_value=campaign
        ), patch.object(routes, 'expire_ambiguous_recipient_claims', return_value=0), patch.object(
            routes, 'MetaWhatsAppService', return_value=service
        ), patch.object(routes, '_find_scoped_media_asset', return_value=media), patch.object(
            routes, '_read_stored_image', return_value=b'image'
        ), patch.object(routes, 'claim_queued_recipient', return_value=recipient), patch.object(
            routes, '_enforce_send_rate_limits'
        ), patch.object(routes, 'refresh_campaign_aggregates', return_value=campaign):
            result = routes._process_campaign_batch()
        self.assertTrue(result['paused'])
        self.assertEqual(recipient.status, 'queued')
        self.assertEqual(campaign.pause_code, '131042')

    def test_one_recipient_failure_does_not_stop_the_next_recipient(self):
        campaign = FakeCampaign(2)
        recipients = [FakeRecipient(1, campaign), FakeRecipient(2, campaign)]
        service = self.configured_service()
        service.send_template.side_effect = [
            MetaWhatsAppError('Recipient failed.', code='131026'),
            {'message_id': 'wamid.success', 'status': 'accepted'},
        ]
        media = SimpleNamespace(id=MEDIA_ID, content_type='image/jpeg')
        with patch.dict(
            os.environ, {**BASE_ENV, 'WHATSAPP_CAMPAIGN_BATCH_SIZE': '3'}, clear=True
        ), patch.object(routes, 'claim_campaign', return_value=campaign), patch.object(
            routes, 'expire_ambiguous_recipient_claims', return_value=0
        ), patch.object(routes, 'MetaWhatsAppService', return_value=service), patch.object(
            routes, '_find_scoped_media_asset', return_value=media
        ), patch.object(routes, '_read_stored_image', return_value=b'image'), patch.object(
            routes, 'claim_queued_recipient', side_effect=[*recipients, None]
        ), patch.object(routes, '_enforce_send_rate_limits'), patch.object(
            routes, 'WhatsAppWebhookEvent'
        ) as webhook, patch.object(
            routes, 'refresh_campaign_aggregates', return_value=campaign
        ), patch.object(routes, 'release_campaign_lease'):
            webhook.objects.return_value.order_by.return_value = []
            result = routes._process_campaign_batch()
        self.assertFalse(result['paused'])
        self.assertEqual(result['failed_in_batch'], 1)
        self.assertEqual(result['accepted_in_batch'], 1)
        self.assertEqual(recipients[0].status, 'failed')
        self.assertEqual(recipients[1].status, 'accepted')

    def test_expired_processing_claims_become_unknown_not_queued(self):
        campaign = FakeCampaign(1)
        collection = MagicMock()
        collection.update_many.return_value.modified_count = 1
        with patch.object(
            campaign_wa.CampaignWhatsAppRecipient,
            '_get_collection',
            return_value=collection,
        ):
            self.assertEqual(campaign_wa.expire_ambiguous_recipient_claims(campaign), 1)
        update = collection.update_many.call_args.args[1]
        self.assertEqual(update['$set']['status'], 'unknown')
        self.assertNotEqual(update['$set']['status'], 'queued')

    def test_paused_campaign_remains_paused_until_explicit_resume(self):
        campaign = FakeCampaign(3)
        campaign.pause_code = '131042'
        campaign.pause_reason = 'Billing issue.'

        class Records:
            def __init__(self, statuses):
                self.statuses = statuses

            def filter(self, **query):
                expected = query.get('status')
                expected_values = query.get('status__in')
                if expected is not None:
                    matches = [status for status in self.statuses if status == expected]
                else:
                    matches = [status for status in self.statuses if status in expected_values]
                return Records(matches)

            def count(self):
                return len(self.statuses)

        objects = MagicMock(return_value=Records(['queued', 'queued', 'accepted']))
        with patch.object(
            campaign_wa, 'CampaignWhatsAppRecipient', SimpleNamespace(objects=objects)
        ):
            campaign_wa.refresh_campaign_aggregates(campaign)
            self.assertEqual(campaign.status, 'paused')
            campaign_wa.resume_campaign(campaign)
            campaign_wa.refresh_campaign_aggregates(campaign)

        self.assertEqual(campaign.status, 'queued')
        self.assertIsNone(campaign.pause_code)
        self.assertIsNone(campaign.pause_reason)


class CampaignProgressTests(unittest.TestCase):
    def test_progress_aggregates_count_every_delivery_state(self):
        campaign = FakeCampaign(8)
        statuses = [
            'queued', 'processing', 'accepted', 'sent',
            'delivered', 'read', 'failed', 'unknown',
        ]

        class Records:
            def __init__(self, values):
                self.values = values

            def filter(self, **query):
                exact = query.get('status')
                accepted = query.get('status__in')
                if exact is not None:
                    return Records([value for value in self.values if value == exact])
                return Records([value for value in self.values if value in accepted])

            def count(self):
                return len(self.values)

        with patch.object(
            campaign_wa,
            'CampaignWhatsAppRecipient',
            SimpleNamespace(objects=MagicMock(return_value=Records(statuses))),
        ):
            campaign_wa.refresh_campaign_aggregates(campaign)

        self.assertEqual(campaign.queued_count, 1)
        self.assertEqual(campaign.processing_count, 1)
        self.assertEqual(campaign.accepted_count, 4)
        self.assertEqual(campaign.sent_count, 3)
        self.assertEqual(campaign.delivered_count, 2)
        self.assertEqual(campaign.read_count, 1)
        self.assertEqual(campaign.failed_count, 1)
        self.assertEqual(campaign.unknown_count, 1)
        self.assertEqual(campaign.status, 'queued')


class CampaignFrontendContractTests(unittest.TestCase):
    def test_offer_campaign_frontend_continues_queue_without_server_secret(self):
        root = Path(__file__).resolve().parents[1]
        component_paths = [
            root / 'frontend' / 'src' / 'components' / 'GeneralCampaign.jsx',
            root / 'frontend' / 'src' / 'components' / 'BirthdayCampaign.jsx',
        ]
        utility = (root / 'frontend' / 'src' / 'utils' / 'campaignQueue.js').read_text(
            encoding='utf-8'
        )
        components = '\n'.join(path.read_text(encoding='utf-8') for path in component_paths)
        offer_campaigns = (
            root / 'frontend' / 'src' / 'components' / 'OfferCampaigns.jsx'
        ).read_text(encoding='utf-8')
        frontend_source = '\n'.join((components, utility, offer_campaigns))

        for forbidden in (
            'wa.me', 'window.open', 'direct_whatsapp',
            'WHATSAPP_CAMPAIGN_WORKER_SECRET', 'CRON_SECRET', 'process-queue-cron',
        ):
            self.assertNotIn(forbidden, frontend_source)
        for required in (
            '/api/campaigns/media',
            '/api/campaigns/send',
            '/api/campaigns/process-queue',
            '/api/campaigns/${campaignId}',
            "delivery_method: 'api'",
            "template_name: CAMPAIGN_TEMPLATE_NAME",
            "language: CAMPAIGN_TEMPLATE_LANGUAGE",
            'media_asset_id: mediaAssetId',
            "'Idempotency-Key': requestId",
        ):
            self.assertIn(required, utility)
        self.assertIn('processQueuedCampaignBatch', offer_campaigns)
        self.assertIn('while (!controller.signal.aborted)', offer_campaigns)
        self.assertIn('queued > 0', offer_campaigns)
        self.assertIn('Campaign started for', components)
        self.assertNotIn('Campaign sent to', components)

    def test_vercel_and_environment_have_no_cron_dependency(self):
        root = Path(__file__).resolve().parents[1]
        vercel_config = json.loads((root / 'vercel.json').read_text(encoding='utf-8'))
        env_example = (root / '.env.example').read_text(encoding='utf-8')
        self.assertNotIn('crons', vercel_config)
        self.assertNotIn('CRON_SECRET', env_example)
        self.assertNotIn('process-queue-cron', json.dumps(vercel_config))


class CampaignWebhookStatusTests(unittest.TestCase):
    class Query:
        def __init__(self, recipient):
            self.recipient = recipient
            self.query = None

        def __call__(self, **query):
            self.query = query
            return self

        def modify(self, new=False, **update):
            if self.recipient.status not in self.query['status__in']:
                return None
            self.recipient.update(**update)
            return self.recipient

    def test_sent_delivered_read_are_monotonic_and_failed_is_bounded(self):
        campaign = FakeCampaign(1)
        recipient = FakeRecipient(1, campaign)
        recipient.status = 'accepted'
        recipient.meta_message_id = 'wamid.status'
        query = self.Query(recipient)
        with patch.object(
            campaign_wa, 'CampaignWhatsAppRecipient', SimpleNamespace(objects=query)
        ), patch.object(campaign_wa, 'refresh_campaign_aggregates') as refresh:
            for status in ('sent', 'delivered', 'read'):
                self.assertTrue(campaign_wa.update_campaign_recipient_status(
                    recipient.meta_message_id, status
                ))
            self.assertFalse(campaign_wa.update_campaign_recipient_status(
                recipient.meta_message_id, 'delivered'
            ))
        self.assertEqual(recipient.status, 'read')
        self.assertEqual(refresh.call_count, 3)

        failed_recipient = FakeRecipient(2, campaign)
        failed_recipient.status = 'accepted'
        failed_recipient.meta_message_id = 'wamid.failed'
        failed_query = self.Query(failed_recipient)
        with patch.object(
            campaign_wa,
            'CampaignWhatsAppRecipient',
            SimpleNamespace(objects=failed_query),
        ), patch.object(campaign_wa, 'refresh_campaign_aggregates'):
            self.assertTrue(campaign_wa.update_campaign_recipient_status(
                failed_recipient.meta_message_id,
                'failed',
                '131000' * 30,
                'safe failure' * 100,
            ))
        self.assertEqual(failed_recipient.status, 'failed')
        self.assertLessEqual(len(failed_recipient.error_code), 100)
        self.assertLessEqual(len(failed_recipient.error_message), 500)


if __name__ == '__main__':
    unittest.main()
