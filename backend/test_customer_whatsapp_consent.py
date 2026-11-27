"""Explicit WhatsApp customer-consent workflow tests with no external I/O."""
import os
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from flask import Flask

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'synthetic-customer-consent-test-secret')

from models import Customer
from routes import campaign_routes, customer_routes
from utils import auth as auth_utils
from utils import invoice_whatsapp


USER = {'role': 'owner', 'user_id': '000000000000000000000001'}
BRANCH = SimpleNamespace(id=ObjectId('000000000000000000000010'))


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def first(self):
        return self.result


class FakeCustomer:
    DoesNotExist = type('DoesNotExist', (Exception,), {})
    existing = None
    saved = []

    def __init__(self, **values):
        self.id = ObjectId()
        self.whatsapp_consent = False
        self.whatsapp_consent_at = None
        self.whatsapp_consent_source = None
        self.whatsapp_consent_revoked_at = None
        self.updated_at = None
        for key, value in values.items():
            setattr(self, key, value)

    @classmethod
    def objects(cls, **_filters):
        return FakeQuery(cls.existing)

    def save(self):
        self.__class__.saved.append(self)
        return self


def invoice_records(customer):
    invoice = SimpleNamespace(
        invoice_status='finalized',
        invoice_number='INV-CONSENT-1',
    )
    bill = SimpleNamespace(
        booking_status='service-completed',
        payment_mode='upi',
        final_amount=500,
        customer=customer,
    )
    return invoice, bill


class CustomerConsentApiTests(unittest.TestCase):
    def setUp(self):
        FakeCustomer.existing = None
        FakeCustomer.saved = []
        app = Flask(__name__)
        app.register_blueprint(customer_routes.customer_bp, url_prefix='/api/customers')
        self.client = app.test_client()
        self.contexts = [
            patch.object(auth_utils, 'get_current_user', return_value=USER),
            patch.object(customer_routes, 'Customer', FakeCustomer),
            patch.object(customer_routes, 'get_selected_branch', return_value=BRANCH),
            patch.object(customer_routes, 'apply_branch_scope', side_effect=lambda query, *_args: query),
        ]
        for context in self.contexts:
            context.start()

    def tearDown(self):
        for context in reversed(self.contexts):
            context.stop()

    def create_customer(self, **extra):
        payload = {
            'mobile': f'98765432{len(FakeCustomer.saved):02d}',
            'firstName': 'Consent',
            'lastName': 'Test',
            **extra,
        }
        return self.client.post('/api/customers/', json=payload)

    def test_new_customer_without_checkbox_remains_not_consented(self):
        response = self.create_customer()
        self.assertEqual(response.status_code, 201)
        customer = FakeCustomer.saved[-1]
        self.assertFalse(customer.whatsapp_consent)
        self.assertIsNone(customer.whatsapp_consent_at)
        self.assertIsNone(customer.whatsapp_consent_source)
        self.assertIsNone(customer.whatsapp_consent_revoked_at)
        self.assertFalse(response.get_json()['whatsappConsent'])

    def test_new_customer_with_checkbox_records_consent_audit(self):
        before = datetime.utcnow()
        response = self.create_customer(whatsappConsent=True)
        after = datetime.utcnow()
        self.assertEqual(response.status_code, 201)
        customer = FakeCustomer.saved[-1]
        self.assertTrue(customer.whatsapp_consent)
        self.assertEqual(customer.whatsapp_consent_source, 'customer_create')
        self.assertLessEqual(before, customer.whatsapp_consent_at)
        self.assertLessEqual(customer.whatsapp_consent_at, after)
        body = response.get_json()
        self.assertTrue(body['whatsappConsent'])
        self.assertEqual(body['whatsappConsentSource'], 'customer_create')
        self.assertIsNotNone(body['whatsappConsentAt'])

    def test_edit_grants_then_revokes_without_losing_original_audit(self):
        customer = FakeCustomer(
            mobile='9876543210',
            first_name='Consent',
            last_name='Test',
            branch=BRANCH,
        )
        FakeCustomer.existing = customer

        grant = self.client.put(
            f'/api/customers/{customer.id}', json={'whatsappConsent': True}
        )
        self.assertEqual(grant.status_code, 200)
        self.assertTrue(customer.whatsapp_consent)
        self.assertEqual(customer.whatsapp_consent_source, 'customer_edit')
        self.assertIsNotNone(customer.whatsapp_consent_at)
        self.assertIsNone(customer.whatsapp_consent_revoked_at)
        original_at = customer.whatsapp_consent_at
        original_source = customer.whatsapp_consent_source

        revoke = self.client.put(
            f'/api/customers/{customer.id}', json={'whatsappConsent': False}
        )
        self.assertEqual(revoke.status_code, 200)
        self.assertFalse(customer.whatsapp_consent)
        self.assertIsNotNone(customer.whatsapp_consent_revoked_at)
        self.assertEqual(customer.whatsapp_consent_at, original_at)
        self.assertEqual(customer.whatsapp_consent_source, original_source)
        self.assertFalse(revoke.get_json()['whatsappConsent'])

    def test_non_boolean_consent_is_rejected(self):
        response = self.create_customer(whatsappConsent='true')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()['error'], 'whatsappConsent must be true or false')
        self.assertEqual(FakeCustomer.saved, [])


class CustomerConsentEligibilityTests(unittest.TestCase):
    def test_model_has_fail_closed_consent_and_audit_fields(self):
        self.assertFalse(Customer._fields['whatsapp_consent'].default)
        for field in (
            'whatsapp_consent_at',
            'whatsapp_consent_source',
            'whatsapp_consent_revoked_at',
        ):
            self.assertIn(field, Customer._fields)

    def test_revoked_customer_is_excluded_from_campaign(self):
        customer = SimpleNamespace(
            id=ObjectId('000000000000000000000020'),
            mobile='9876543210',
            whatsapp_consent=False,
            whatsapp_consent_at=datetime.utcnow(),
            whatsapp_consent_revoked_at=datetime.utcnow(),
        )
        eligible, excluded = campaign_routes._classify_campaign_customers(
            [customer], [str(customer.id)]
        )
        self.assertEqual(eligible, [])
        self.assertEqual(excluded['excluded_no_consent'], 1)

    def test_revoked_customer_invoice_is_skipped_and_opted_in_is_eligible(self):
        customer = SimpleNamespace(
            first_name='Priya',
            last_name='K',
            mobile='9840030803',
            whatsapp_consent=False,
            whatsapp_consent_at=datetime.utcnow(),
            whatsapp_consent_revoked_at=datetime.utcnow(),
        )
        invoice, bill = invoice_records(customer)
        with self.assertRaises(invoice_whatsapp.InvoiceWhatsAppEligibilityError) as revoked:
            invoice_whatsapp._eligible_invoice(invoice, bill)
        self.assertEqual(revoked.exception.code, 'whatsapp_consent_required')

        customer.whatsapp_consent = True
        customer.whatsapp_consent_revoked_at = None
        eligible = invoice_whatsapp._eligible_invoice(invoice, bill)
        self.assertIs(eligible['customer'], customer)
        self.assertEqual(eligible['phone'], '919840030803')

    def test_frontend_requires_explicit_unchecked_consent(self):
        root = Path(__file__).resolve().parents[1] / 'frontend' / 'src' / 'components'
        customer_list = (root / 'CustomerList.jsx').read_text(encoding='utf-8')
        quick_sale = (root / 'QuickSale.jsx').read_text(encoding='utf-8')
        label = 'Customer agrees to receive WhatsApp messages from Priyanka Nature Cure'
        for source in (customer_list, quick_sale):
            self.assertIn(label, source)
            self.assertIn('whatsappConsent: false', source)
            self.assertNotIn('defaultChecked', source)
        self.assertIn('whatsappConsent: customerFormData.whatsappConsent === true', customer_list)
        self.assertIn('whatsappConsent: newCustomerData.whatsappConsent === true', quick_sale)


if __name__ == '__main__':
    unittest.main()
