"""Persisted end-to-end coverage for automatic invoice share links."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import mongomock
from flask import Flask
from mongoengine import connect, disconnect

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'synthetic-invoice-share-test-secret')

from models import (  # noqa: E402
    Bill,
    Branch,
    Customer,
    Invoice,
    InvoiceLifecycleEvent,
    WhatsAppInvoiceNotification,
)
from routes import bill_routes  # noqa: E402
from services.invoice_pdf_service import register_template_filters  # noqa: E402
from utils import auth as auth_utils  # noqa: E402
from utils import invoice_whatsapp as invoice_wa  # noqa: E402
from utils.meta_whatsapp_service import (  # noqa: E402
    SALON_PRODUCTION_PHONE_NUMBER_ID,
    SALON_PRODUCTION_WABA_ID,
)


ENV = {
    'APP_RUNTIME': 'production',
    'MONGODB_URI': 'mongodb://localhost:27017',
    'MONGODB_DB': 'invoice_share_e2e',
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


class FakeMetaResponse:
    status_code = 200
    headers = {}

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class InvoicePublicShareEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect(alias='default')
        connect(
            'invoice_share_e2e',
            alias='default',
            host='mongodb://localhost',
            mongo_client_class=mongomock.MongoClient,
        )
        cls.app = Flask(__name__, template_folder='templates')
        register_template_filters(cls.app)
        cls.app.register_blueprint(bill_routes.bill_bp, url_prefix='/api')
        cls.app.add_url_rule(
            '/i/<share_code>',
            'short_invoice_view_e2e',
            bill_routes.short_invoice_view,
            methods=['GET'],
        )
        cls.app.add_url_rule(
            '/i/<share_code>/pdf',
            'short_invoice_pdf_e2e',
            bill_routes.short_invoice_pdf,
            methods=['GET'],
        )
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        for model in (
            WhatsAppInvoiceNotification,
            InvoiceLifecycleEvent,
            Invoice,
            Bill,
            Customer,
            Branch,
        ):
            model.drop_collection()
        disconnect(alias='default')

    def setUp(self):
        for model in (
            WhatsAppInvoiceNotification,
            InvoiceLifecycleEvent,
            Invoice,
            Bill,
            Customer,
            Branch,
        ):
            model.drop_collection()
        self.env = patch.dict(os.environ, ENV, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _records(self, suffix, *, finalized=True):
        branch = Branch(name=f'E2E Branch {suffix}', city='Chennai').save()
        customer = Customer(
            mobile=f'984003{suffix:04d}',
            first_name='Priya',
            last_name='K',
            branch=branch,
            whatsapp_consent=True,
        ).save()
        bill = Bill(
            bill_number=f'E2E-BILL-{suffix}',
            customer=customer,
            branch=branch,
            final_amount=1250.50,
            payment_mode='upi',
            booking_status='service-completed',
        ).save()
        invoice_number = f'E2E-INV-{suffix}'
        invoice = Invoice(
            bill=bill,
            invoice_number=invoice_number,
            customer=customer,
            branch=branch,
            invoice_data={
                'invoice_number': invoice_number,
                'bill_number': bill.bill_number,
                'booking_date': '27 Nov 2026',
                'booking_time': '10:00 AM',
                'customer': {
                    'name': 'Priya K',
                    'mobile': customer.mobile,
                    'wallet_balance': 0,
                },
                'branch': {
                    'name': branch.name,
                    'address': '',
                    'city': 'Chennai',
                    'phone': '',
                    'gstin': '',
                },
                'items': [],
                'summary': {
                    'subtotal': 1250.50,
                    'discount': 0,
                    'net': 1250.50,
                    'tax': 0,
                    'total': 1250.50,
                },
                'payment': {
                    'status': 'paid',
                    'mode': 'upi',
                    'amount': 1250.50,
                },
            },
            status='generated',
            invoice_status=(
                'finalized' if finalized
                else 'awaiting_customer_confirmation'
            ),
            signature_status='skipped' if finalized else 'pending',
            skip_reason='Synthetic end-to-end test' if finalized else None,
            snapshot_hash='a' * 64,
        ).save()
        bill.invoice = invoice
        bill.save()
        return invoice, bill

    def test_automatic_send_code_resolves_public_html_and_pdf(self):
        invoice, bill = self._records(1001, finalized=False)
        captured = {'message_posts': 0}

        def meta_request(method, url, **kwargs):
            if method == 'GET' and url.endswith('/message_templates'):
                return FakeMetaResponse({'data': [{
                    'id': '1',
                    'name': 'priyanka_invoice_paid',
                    'status': 'APPROVED',
                    'category': 'UTILITY',
                    'language': 'en_US',
                    'components': [],
                }]})
            if method == 'POST' and url.endswith('/messages'):
                captured['message_posts'] += 1
                components = kwargs['json']['template']['components']
                captured['url_button_parameter'] = next(
                    component['parameters'][0]['text']
                    for component in components
                    if component.get('type') == 'button'
                )
                return FakeMetaResponse({
                    'messages': [{'id': 'wamid.synthetic.public-link'}],
                })
            raise AssertionError(f'Unexpected external Meta request: {method}')

        with patch.object(
            auth_utils,
            'get_current_user',
            return_value={'role': 'owner', 'user_id': '1'},
        ), patch(
            'utils.meta_whatsapp_service.requests.request',
            side_effect=meta_request,
        ):
            finalize = self.client.post(
                f'/api/bills/{bill.id}/signature',
                json={
                    'action': 'skip',
                    'skip_reason': 'Synthetic end-to-end test',
                    'invoice_version': invoice.invoice_version,
                    'snapshot_hash': invoice.snapshot_hash,
                    'idempotency_key': 'synthetic-finalization-1001',
                },
            )

        self.assertEqual(finalize.status_code, 200)
        result = finalize.get_json()['whatsapp_invoice']
        self.assertEqual(result, {'status': 'accepted'})
        self.assertEqual(captured['message_posts'], 1)
        button_code = captured['url_button_parameter']
        self.assertRegex(button_code, r'^[A-Za-z0-9_-]{8}$')
        self.assertNotIn('/i/', button_code)
        self.assertNotIn('http', button_code.lower())
        self.assertNotIn('?', button_code)

        invoice.reload()
        self.assertEqual(invoice.invoice_status, 'finalized')
        self.assertEqual(invoice.share_code, button_code)
        share_index = next(
            details
            for details in Invoice._get_collection().index_information().values()
            if details.get('key') == [('share_code', 1)]
        )
        self.assertTrue(share_index.get('unique'))
        self.assertTrue(share_index.get('sparse'))
        notification = WhatsAppInvoiceNotification.objects.get(invoice=invoice)
        self.assertEqual(notification.share_code, button_code)

        view = self.client.get(f'/i/{button_code}')
        self.assertEqual(view.status_code, 200)
        self.assertIn(invoice.invoice_number.encode(), view.data)
        self.assertIn(b'Save Invoice as PDF', view.data)

        pdf = self.client.get(f'/i/{button_code}/pdf')
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, 'application/pdf')
        self.assertTrue(pdf.data.startswith(b'%PDF'))

        stable_code = invoice_wa.ensure_invoice_share_code(invoice)
        self.assertEqual(stable_code, button_code)
        with patch.object(
            invoice_wa.secrets,
            'token_urlsafe',
            side_effect=AssertionError('duplicate send regenerated share code'),
        ), patch(
            'utils.meta_whatsapp_service.requests.request',
            side_effect=AssertionError('duplicate notification called Meta'),
        ):
            duplicate = invoice_wa.try_send_paid_invoice_whatsapp(invoice, bill)
        self.assertEqual(duplicate, {'status': 'accepted', 'duplicate': True})
        invoice.reload()
        self.assertEqual(invoice.share_code, button_code)

    def test_invalid_and_pending_short_links_are_inaccessible(self):
        self.assertEqual(self.client.get('/i/not-valid').status_code, 404)
        pending, _ = self._records(1002, finalized=False)
        pending.share_code = 'Pending1'
        pending.save()
        self.assertEqual(self.client.get('/i/Pending1').status_code, 409)
        self.assertEqual(self.client.get('/i/Pending1/pdf').status_code, 409)

    def test_crm_html_hides_legacy_actions_but_public_keeps_pdf(self):
        invoice, bill = self._records(1003)
        invoice.share_code = 'Public01'
        invoice.save()
        with patch.object(
            auth_utils,
            'get_current_user',
            return_value={'role': 'owner', 'user_id': '1'},
        ):
            crm_html = self.client.get(f'/api/bills/{bill.id}/invoice/html')
        self.assertEqual(crm_html.status_code, 200)
        self.assertNotIn(b'Send via WhatsApp', crm_html.data)
        self.assertNotIn(b'Save Invoice as PDF', crm_html.data)

        public_html = self.client.get('/i/Public01')
        self.assertEqual(public_html.status_code, 200)
        self.assertIn(b'Save Invoice as PDF', public_html.data)

    def test_react_invoice_ui_has_no_legacy_distribution_actions(self):
        frontend_components = Path(__file__).resolve().parent.parent / 'frontend' / 'src' / 'components'
        source = '\n'.join(
            (frontend_components / name).read_text(encoding='utf-8')
            for name in ('SignatureSection.jsx', 'InvoicePreview.jsx')
        )
        self.assertNotIn('Download Bill', source)
        self.assertNotIn('Send via WhatsApp', source)
        self.assertNotIn('wa.me', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
