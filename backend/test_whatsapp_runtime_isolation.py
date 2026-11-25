"""Fail-closed runtime isolation tests without external connections."""
import os
import unittest
from unittest.mock import MagicMock, patch

from services.r2_media_service import R2MediaConfigurationError, R2MediaService
from utils.env_config import (
    RuntimeConfigurationError,
    get_app_runtime,
    get_jwt_secret,
    get_mongodb_db,
    get_mongodb_uri,
)
from utils.meta_whatsapp_service import (
    MetaWhatsAppError,
    MetaWhatsAppService,
    SALON_DEMO_PHONE_NUMBER_ID,
    SALON_DEMO_WABA_ID,
    SALON_PRODUCTION_PHONE_NUMBER_ID,
    SALON_PRODUCTION_WABA_ID,
)


BASE_ENV = {
    'MONGODB_URI': 'mongodb://production.invalid',
    'MONGODB_DB': 'Saloon_prod',
    'JWT_SECRET': 'synthetic-production-jwt',
    'MONGODB_URI_DEMO': 'mongodb://demo.invalid',
    'MONGODB_DB_DEMO': 'Saloon_demo',
    'JWT_SECRET_DEMO': 'synthetic-demo-jwt',
    'META_GRAPH_API_VERSION': 'v26.0',
    'META_WA_ACCESS_TOKEN': 'synthetic-token',
    'META_WA_APP_SECRET': 'synthetic-app-secret',
    'META_WA_WEBHOOK_VERIFY_TOKEN': 'synthetic-verify-token',
    'R2_ACCESS_KEY_ID': 'synthetic-access-key',
    'R2_SECRET_ACCESS_KEY': 'synthetic-secret-key',
    'R2_ENDPOINT': 'https://example-account.r2.cloudflarestorage.com',
}


class WhatsAppRuntimeIsolationTests(unittest.TestCase):
    def test_runtime_must_be_explicit_and_exact(self):
        for value in (None, '', 'staging', ' production ', 'PRODUCTION'):
            environment = {} if value is None else {'APP_RUNTIME': value}
            with self.subTest(value=value), patch.dict(
                os.environ, environment, clear=True,
            ), self.assertRaises(RuntimeConfigurationError):
                get_app_runtime()

    def test_demo_selects_only_demo_database_and_jwt(self):
        with patch.dict(os.environ, {**BASE_ENV, 'APP_RUNTIME': 'demo'}, clear=True):
            self.assertEqual(get_mongodb_uri(), BASE_ENV['MONGODB_URI_DEMO'])
            self.assertEqual(get_mongodb_db(), 'Saloon_demo')
            self.assertEqual(get_jwt_secret(), BASE_ENV['JWT_SECRET_DEMO'])

        missing_demo = {**BASE_ENV, 'APP_RUNTIME': 'demo'}
        missing_demo.pop('MONGODB_URI_DEMO')
        with patch.dict(os.environ, missing_demo, clear=True), self.assertRaises(RuntimeError):
            get_mongodb_uri()

    def test_production_selects_only_production_database_and_jwt(self):
        with patch.dict(
            os.environ, {**BASE_ENV, 'APP_RUNTIME': 'production'}, clear=True,
        ):
            self.assertEqual(get_mongodb_uri(), BASE_ENV['MONGODB_URI'])
            self.assertEqual(get_mongodb_db(), 'Saloon_prod')
            self.assertEqual(get_jwt_secret(), BASE_ENV['JWT_SECRET'])

        invalid = {**BASE_ENV, 'APP_RUNTIME': 'production', 'MONGODB_DB': 'Saloon_demo'}
        with patch.dict(os.environ, invalid, clear=True), self.assertRaises(
            RuntimeConfigurationError
        ):
            get_mongodb_db()

    def test_meta_identity_cannot_cross_runtimes(self):
        demo = {
            **BASE_ENV,
            'APP_RUNTIME': 'demo',
            'META_WA_BUSINESS_ACCOUNT_ID': SALON_DEMO_WABA_ID,
            'META_WA_PHONE_NUMBER_ID': SALON_DEMO_PHONE_NUMBER_ID,
        }
        with patch.dict(os.environ, demo, clear=True):
            MetaWhatsAppService(production=False).assert_configured()
            with self.assertRaises(MetaWhatsAppError):
                MetaWhatsAppService(production=True)

        production = {
            **BASE_ENV,
            'APP_RUNTIME': 'production',
            'META_WA_BUSINESS_ACCOUNT_ID': SALON_PRODUCTION_WABA_ID,
            'META_WA_PHONE_NUMBER_ID': SALON_PRODUCTION_PHONE_NUMBER_ID,
        }
        with patch.dict(os.environ, production, clear=True):
            MetaWhatsAppService(production=True).assert_configured()
            with self.assertRaises(MetaWhatsAppError):
                MetaWhatsAppService(production=False)

    def test_r2_bucket_cannot_cross_runtimes(self):
        demo = {
            **BASE_ENV,
            'APP_RUNTIME': 'demo',
            'R2_BUCKET_NAME': 'airalexo-salon-media-demo',
        }
        R2MediaService(client=MagicMock(), environ=demo, production=False)
        with self.assertRaises(R2MediaConfigurationError):
            R2MediaService(client=MagicMock(), environ=demo, production=True)

        production = {
            **BASE_ENV,
            'APP_RUNTIME': 'production',
            'R2_BUCKET_NAME': 'airalexo-salon-media-production',
        }
        R2MediaService(client=MagicMock(), environ=production, production=True)
        with self.assertRaises(R2MediaConfigurationError):
            R2MediaService(client=MagicMock(), environ=production, production=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
