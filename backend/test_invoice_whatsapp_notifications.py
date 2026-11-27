"""Paid-invoice WhatsApp notification tests with no external I/O."""
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask
from mongoengine.errors import NotUniqueError

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'synthetic-invoice-test-jwt-secret')

from routes import bill_routes
from utils import auth as auth_utils
from utils import invoice_whatsapp as invoice_wa
from utils.meta_whatsapp_service import (
    MetaWhatsAppError,
    MetaWhatsAppService,
    SALON_PRODUCTION_PHONE_NUMBER_ID,
    SALON_PRODUCTION_WABA_ID,
    extract_webhook_events,
)


ENV = {
    'APP_RUNTIME': 'production',
    'META_GRAPH_API_VERSION': 'v26.0',
    'META_WA_ACCESS_TOKEN': 'synthetic-access-token',
    'META_WA_PHONE_NUMBER_ID': SALON_PRODUCTION_PHONE_NUMBER_ID,
    'META_WA_BUSINESS_ACCOUNT_ID': SALON_PRODUCTION_WABA_ID,
    'META_WA_APP_SECRET': 'synthetic-app-secret',
    'META_WA_WEBHOOK_VERIFY_TOKEN': 'synthetic-verify-token',
    'WHATSAPP_INVOICE_NOTIFICATIONS_ENABLED': 'true',
    'META_WA_INVOICE_TEMPLATE_NAME': 'priyanka_invoice_paid',
    'META_WA_INVOICE_TEMPLATE_LANGUAGE': 'en_US',
}


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class FakeNotification:
    def __init__(self, invoice, bill, customer):
        self.id = '000000000000000000000090'
        self.invoice = invoice
        self.bill = bill
        self.customer = customer
        self.status = 'pending'
        self.last_error_code = None
        self.meta_message_id = None

    def update(self, **operations):
        for operation, value in operations.items():
            if operation.startswith('set__'):
                setattr(self, operation[5:], value)


def make_records(**overrides):
    customer = SimpleNamespace(
        id='000000000000000000000003',
        first_name='Priya',
        last_name='K',
        mobile='9840030803',
        whatsapp_consent=True,
    )
    bill = SimpleNamespace(
        id='000000000000000000000002',
        booking_status='service-completed',
        payment_mode='upi',
        final_amount=1250.5,
        customer=customer,
        branch=SimpleNamespace(id='000000000000000000000004'),
    )
    invoice = SimpleNamespace(
        id='000000000000000000000001',
        invoice_status='finalized',
        invoice_number='INV-1001',
        share_code='Share123',
        status='shared',
    )
    for key, value in overrides.items():
        target, field = key.split('__', 1)
        setattr({'invoice': invoice, 'bill': bill, 'customer': customer}[target], field, value)
    return invoice, bill, customer


class InvoiceWhatsAppTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, ENV, clear=True))

    def _service(self):
        service = MagicMock()
        service.business_account_id = SALON_PRODUCTION_WABA_ID
        service.phone_number_id = SALON_PRODUCTION_PHONE_NUMBER_ID
        service.get_templates.return_value = [{
            'name': 'priyanka_invoice_paid',
            'language': 'en_US',
            'status': 'APPROVED',
            'category': 'UTILITY',
        }]
        service.send_template.return_value = {
            'message_id': 'wamid.synthetic.invoice',
            'status': 'accepted',
        }
        return service

    def test_feature_flag_off_performs_no_work(self):
        invoice, bill, _ = make_records()
        with patch.dict(os.environ, {'WHATSAPP_INVOICE_NOTIFICATIONS_ENABLED': 'false'}), patch.object(
            invoice_wa, 'MetaWhatsAppService'
        ) as service, patch.object(invoice_wa, 'ensure_invoice_share_code') as share:
            result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertIsNone(result)
        service.assert_not_called()
        share.assert_not_called()

    def test_demo_runtime_cannot_use_production_invoice_sender(self):
        invoice, bill, _ = make_records()
        with patch.dict(os.environ, {'APP_RUNTIME': 'demo'}), patch.object(
            invoice_wa, 'MetaWhatsAppService'
        ) as service:
            result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertEqual(result, {
            'status': 'skipped',
            'reason': 'production_runtime_required',
        })
        service.assert_not_called()

    def test_ineligible_invoice_states_never_send(self):
        cases = [
            {'invoice__invoice_status': 'awaiting_customer_confirmation'},
            {'bill__booking_status': 'confirmed'},
            {'bill__payment_mode': ''},
            {'bill__final_amount': 0},
            {'bill__customer': None},
            {'customer__mobile': 'not-a-phone'},
            {'customer__whatsapp_consent': False},
        ]
        with patch.object(invoice_wa, 'MetaWhatsAppService') as service:
            for overrides in cases:
                with self.subTest(overrides=overrides):
                    invoice, bill, _ = make_records(**overrides)
                    result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
                    self.assertEqual(result['status'], 'skipped')
        service.assert_not_called()

    def test_indian_phone_normalization_is_strict(self):
        self.assertEqual(
            invoice_wa.normalize_indian_whatsapp_phone('+91 98400 30803'),
            '919840030803',
        )
        self.assertEqual(
            invoice_wa.normalize_indian_whatsapp_phone('09840030803'),
            '919840030803',
        )
        for invalid in ('', '12345', '+1 202 555 0110', '98400ABC03'):
            self.assertIsNone(invoice_wa.normalize_indian_whatsapp_phone(invalid))

    def test_existing_share_code_is_reused_and_pending_invoice_is_rejected(self):
        invoice, _, _ = make_records()
        with patch.object(invoice_wa.Invoice, '_get_collection') as collection:
            self.assertEqual(invoice_wa.ensure_invoice_share_code(invoice), 'Share123')
        collection.assert_not_called()

        invoice.invoice_status = 'awaiting_customer_confirmation'
        with self.assertRaises(invoice_wa.InvoiceWhatsAppEligibilityError):
            invoice_wa.ensure_invoice_share_code(invoice)

    def test_share_code_is_atomically_generated_once(self):
        invoice, _, _ = make_records(invoice__share_code='', invoice__status='generated')
        collection = MagicMock()
        collection.find_one_and_update.return_value = {'share_code': 'AbCd1234'}
        with patch.object(
            invoice_wa.Invoice, '_get_collection', return_value=collection
        ), patch.object(
            invoice_wa.secrets, 'token_urlsafe', return_value='AbCd1234'
        ):
            first = invoice_wa.ensure_invoice_share_code(invoice)
            second = invoice_wa.ensure_invoice_share_code(invoice)
        self.assertEqual((first, second), ('AbCd1234', 'AbCd1234'))
        collection.find_one_and_update.assert_called_once()

    def test_share_link_route_uses_the_common_share_code_helper(self):
        invoice, bill, _ = make_records()
        app = Flask(__name__)
        app.register_blueprint(bill_routes.bill_bp, url_prefix='/api')
        invoice_query = MagicMock()
        invoice_query.first.return_value = invoice
        with patch.object(
            auth_utils,
            'get_current_user',
            return_value={'role': 'owner', 'user_id': '1'},
        ), patch.object(
            bill_routes.Bill, 'objects'
        ) as bills, patch.object(
            bill_routes.Invoice, 'objects', return_value=invoice_query
        ), patch.object(
            bill_routes, 'ensure_invoice_share_code', return_value='Share123'
        ) as ensure, patch.object(bill_routes, 'mark_invoice_shared') as mark_shared:
            bills.get.return_value = bill
            response = app.test_client().post(
                f'/api/bills/{bill.id}/share-link'
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'share_code': 'Share123'})
        ensure.assert_called_once_with(invoice)
        mark_shared.assert_called_once_with(invoice)

    def test_paid_invoice_payload_uses_body_order_and_share_code_suffix_only(self):
        captured = {}

        def request_func(method, url, **kwargs):
            captured.update(kwargs['json'])
            return FakeResponse({'messages': [{'id': 'wamid.synthetic.invoice'}]})

        service = MetaWhatsAppService(production=True, request_func=request_func)
        service.send_template(
            '919840030803',
            'priyanka_invoice_paid',
            'en_US',
            body_parameters=['Priya K', '1250.50', 'INV-1001'],
            url_button_parameter='Share123',
        )
        template = captured['template']
        self.assertEqual(template['name'], 'priyanka_invoice_paid')
        self.assertEqual(template['language'], {'code': 'en_US'})
        self.assertEqual(
            template['components'][0]['parameters'],
            [
                {'type': 'text', 'text': 'Priya K'},
                {'type': 'text', 'text': '1250.50'},
                {'type': 'text', 'text': 'INV-1001'},
            ],
        )
        button_text = template['components'][1]['parameters'][0]['text']
        self.assertEqual(button_text, 'Share123')
        self.assertNotIn('http', button_text.lower())
        with self.assertRaises(MetaWhatsAppError) as full_url:
            service.send_template(
                '919840030803',
                'priyanka_invoice_paid',
                'en_US',
                body_parameters=['Priya K', '1250.50', 'INV-1001'],
                url_button_parameter='https://saloon-sandy-gamma.vercel.app/i/Share123',
            )
        self.assertEqual(full_url.exception.code, 'template_parameters_invalid')

    def test_existing_image_header_template_payload_is_unchanged(self):
        captured = {}

        def request_func(method, url, **kwargs):
            captured.update(kwargs['json'])
            return FakeResponse({'messages': [{'id': 'wamid.synthetic.image'}]})

        MetaWhatsAppService(production=True, request_func=request_func).send_template(
            '919840030803', 'promotion_image', 'en_US', media_id='123456789'
        )
        self.assertEqual(captured['template']['components'], [{
            'type': 'header',
            'parameters': [{'type': 'image', 'image': {'id': '123456789'}}],
        }])

    def test_finalized_paid_invoice_is_reserved_and_accepted(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        service = self._service()
        with patch.object(
            invoice_wa, '_reserve_notification', return_value=(notification, True)
        ), patch.object(
            invoice_wa, 'ensure_invoice_share_code', return_value='Share123'
        ), patch.object(
            invoice_wa, 'MetaWhatsAppService', return_value=service
        ), patch.object(
            invoice_wa, 'mark_invoice_shared'
        ) as mark_shared, patch.object(invoice_wa, '_record_lifecycle') as audit:
            result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)

        self.assertEqual(result, {'status': 'accepted'})
        service.send_template.assert_called_once_with(
            '919840030803',
            'priyanka_invoice_paid',
            'en_US',
            body_parameters=['Priya K', '1250.50', 'INV-1001'],
            url_button_parameter='Share123',
        )
        mark_shared.assert_called_once_with(invoice)
        audit.assert_called_once_with(notification, 'invoice_whatsapp_accepted')

    def test_concurrent_reservation_allows_only_one_send(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        service = self._service()
        with patch.object(
            invoice_wa,
            '_reserve_notification',
            side_effect=[(notification, True), (notification, False)],
        ), patch.object(
            invoice_wa, 'ensure_invoice_share_code', return_value='Share123'
        ), patch.object(
            invoice_wa, 'MetaWhatsAppService', return_value=service
        ), patch.object(invoice_wa, '_record_lifecycle'):
            first = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
            second = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertEqual(first['status'], 'accepted')
        self.assertTrue(second['duplicate'])
        service.send_template.assert_called_once()

    def test_atomic_reservation_returns_existing_record_on_unique_collision(self):
        invoice, bill, customer = make_records()
        candidate = MagicMock()
        candidate.save.side_effect = NotUniqueError('synthetic collision')
        existing = FakeNotification(invoice, bill, customer)
        model = MagicMock(return_value=candidate)
        model.objects.return_value.first.return_value = existing
        with patch.object(invoice_wa, 'WhatsAppInvoiceNotification', model):
            reserved, created = invoice_wa._reserve_notification(
                invoice,
                bill,
                customer,
                'priyanka_invoice_paid',
                'en_US',
                attempt_kind='automatic',
                idempotency_key='automatic',
            )
        self.assertIs(reserved, existing)
        self.assertFalse(created)
        candidate.save.assert_called_once_with(force_insert=True)
        model.objects.assert_called_once_with(
            invoice=invoice,
            notification_type='invoice_paid',
            idempotency_key='automatic',
        )

    def test_unapproved_template_is_recorded_without_sending(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        service = self._service()
        service.get_templates.return_value = []
        with patch.object(
            invoice_wa, '_reserve_notification', return_value=(notification, True)
        ), patch.object(
            invoice_wa, 'ensure_invoice_share_code', return_value='Share123'
        ), patch.object(
            invoice_wa, 'MetaWhatsAppService', return_value=service
        ), patch.object(invoice_wa, '_record_lifecycle'):
            result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertEqual(result, {
            'status': 'failed',
            'error_code': 'template_not_approved',
        })
        service.send_template.assert_not_called()

    def test_failed_meta_send_is_recorded_without_raising(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        service = self._service()
        service.send_template.side_effect = MetaWhatsAppError(
            'synthetic failure', code='synthetic_meta_error'
        )
        with patch.object(
            invoice_wa, '_reserve_notification', return_value=(notification, True)
        ), patch.object(
            invoice_wa, 'ensure_invoice_share_code', return_value='Share123'
        ), patch.object(
            invoice_wa, 'MetaWhatsAppService', return_value=service
        ), patch.object(invoice_wa, '_record_lifecycle') as audit:
            result = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertEqual(result, {
            'status': 'failed',
            'error_code': 'synthetic_meta_error',
        })
        audit.assert_called_once_with(notification, 'invoice_whatsapp_failed')

    def test_finalization_response_survives_unexpected_notification_error(self):
        invoice, bill, _ = make_records()
        with patch.object(
            bill_routes, '_finalize_result', return_value={'success': True}
        ), patch.object(
            bill_routes,
            'try_send_paid_invoice_whatsapp',
            side_effect=RuntimeError('must not escape'),
        ):
            result = bill_routes._finalize_result_with_whatsapp(invoice, bill)
        self.assertTrue(result['success'])
        self.assertEqual(result['whatsapp_invoice'], {
            'status': 'failed',
            'error_code': 'internal_error',
        })

    def test_resend_foundation_requires_role_and_remains_disabled(self):
        app = Flask(__name__)
        app.register_blueprint(bill_routes.bill_bp, url_prefix='/api')
        client = app.test_client()
        path = '/api/bills/000000000000000000000001/whatsapp-invoice/resend'

        with patch.object(auth_utils, 'get_current_user', return_value=None):
            self.assertEqual(client.post(path).status_code, 401)
        with patch.object(
            auth_utils,
            'get_current_user',
            return_value={'role': 'staff', 'user_id': '1'},
        ):
            self.assertEqual(client.post(path).status_code, 403)
        with patch.object(
            auth_utils,
            'get_current_user',
            return_value={'role': 'owner', 'user_id': '1'},
        ), patch.object(bill_routes.Bill, 'objects') as bills:
            response = client.post(path)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['error'], 'invoice_whatsapp_resend_disabled')
        bills.assert_not_called()

    def test_webhook_status_updates_are_monotonic_and_account_scoped(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        account = {
            'waba_id': SALON_PRODUCTION_WABA_ID,
            'phone_number_id': SALON_PRODUCTION_PHONE_NUMBER_ID,
        }
        cases = [
            ('sent', ['pending', 'accepted'], None),
            ('delivered', ['pending', 'accepted', 'sent'], 'invoice_whatsapp_delivered'),
            ('read', ['pending', 'accepted', 'sent', 'delivered'], 'invoice_whatsapp_read'),
            ('failed', ['pending', 'accepted', 'sent'], 'invoice_whatsapp_failed'),
        ]
        for status, allowed, audit_type in cases:
            query = MagicMock()
            query.modify.return_value = notification
            with self.subTest(status=status), patch.object(
                invoice_wa.WhatsAppInvoiceNotification,
                'objects',
                return_value=query,
            ) as objects, patch.object(invoice_wa, '_record_lifecycle') as audit:
                updated = invoice_wa.update_invoice_notification_status(
                    'wamid.synthetic.invoice', status, '131000', account=account
                )
            self.assertTrue(updated)
            objects.assert_called_once_with(
                meta_message_id='wamid.synthetic.invoice',
                status__in=allowed,
                **account,
            )
            if audit_type:
                audit.assert_called_once_with(notification, audit_type)
            else:
                audit.assert_not_called()

        query = MagicMock()
        query.modify.return_value = None
        with patch.object(
            invoice_wa.WhatsAppInvoiceNotification,
            'objects',
            return_value=query,
        ), patch.object(invoice_wa, '_record_lifecycle') as ignored_audit:
            self.assertFalse(invoice_wa.update_invoice_notification_status(
                'wamid.unknown', 'read', account=account
            ))
        ignored_audit.assert_not_called()

    def test_wrong_waba_or_phone_id_is_ignored_before_notification_lookup(self):
        def payload(waba_id, phone_number_id):
            return {
                'object': 'whatsapp_business_account',
                'entry': [{
                    'id': waba_id,
                    'changes': [{
                        'field': 'messages',
                        'value': {
                            'messaging_product': 'whatsapp',
                            'metadata': {'phone_number_id': phone_number_id},
                            'statuses': [{
                                'id': 'wamid.synthetic.invoice',
                                'status': 'delivered',
                                'timestamp': '1',
                            }],
                        },
                    }],
                }],
            }

        self.assertEqual(extract_webhook_events(
            payload('9999999999999999', SALON_PRODUCTION_PHONE_NUMBER_ID),
            expected_waba_id=SALON_PRODUCTION_WABA_ID,
            expected_phone_number_id=SALON_PRODUCTION_PHONE_NUMBER_ID,
        ), [])
        self.assertEqual(extract_webhook_events(
            payload(SALON_PRODUCTION_WABA_ID, '9999999999999999'),
            expected_waba_id=SALON_PRODUCTION_WABA_ID,
            expected_phone_number_id=SALON_PRODUCTION_PHONE_NUMBER_ID,
        ), [])

    def test_results_do_not_expose_credentials_or_customer_phone(self):
        invoice, bill, customer = make_records()
        notification = FakeNotification(invoice, bill, customer)
        service = self._service()
        with patch.object(
            invoice_wa, '_reserve_notification', return_value=(notification, True)
        ), patch.object(
            invoice_wa, 'ensure_invoice_share_code', return_value='Share123'
        ), patch.object(
            invoice_wa, 'MetaWhatsAppService', return_value=service
        ), patch.object(invoice_wa, '_record_lifecycle'):
            serialized = json.dumps(invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill))
        for forbidden in (
            customer.mobile,
            ENV['META_WA_ACCESS_TOKEN'],
            ENV['META_WA_APP_SECRET'],
            ENV['META_WA_WEBHOOK_VERIFY_TOKEN'],
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == '__main__':
    unittest.main(verbosity=2)
