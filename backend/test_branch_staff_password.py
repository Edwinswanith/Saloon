import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bson import ObjectId
from flask import Flask

os.environ.setdefault('APP_RUNTIME', 'production')
os.environ.setdefault('JWT_SECRET', 'branch-staff-password-test-secret')

from routes import auth_routes
from utils.auth import hash_password


class BranchStaffPasswordTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.staff_password_hash = hash_password('existing@456')
        self.branch_password_hash = hash_password('test@123')

    def _login(self, password, selected_branch):
        home_branch = SimpleNamespace(
            id=ObjectId(),
            name='Main Road',
            city='Chennai',
            staff_login_password_hash=None,
        )
        staff = SimpleNamespace(
            id=ObjectId(),
            mobile='9000000001',
            email='staff@example.test',
            first_name='Test',
            last_name='Staff',
            role='staff',
            status='active',
            is_active=True,
            password_hash=self.staff_password_hash,
            branch=home_branch,
        )

        staff_model = MagicMock()
        staff_model.objects.return_value.first.return_value = staff
        branch_model = MagicMock()
        branch_model.objects.return_value.first.return_value = selected_branch
        login_history = MagicMock()

        body = {
            'user_type': 'staff',
            'identifier': staff.mobile,
            'password': password,
            'branch_id': str(selected_branch.id),
        }
        with self.app.test_request_context('/api/auth/login', method='POST', json=body):
            with patch.multiple(
                auth_routes,
                Staff=staff_model,
                Branch=branch_model,
                LoginHistory=login_history,
                get_demo_branch_for_user=MagicMock(return_value=None),
                generate_jwt_token=MagicMock(return_value='test-token'),
            ):
                result = auth_routes.login()

        response, status = result if isinstance(result, tuple) else (result, 200)
        return status, response.get_json(), login_history

    def test_configured_branch_accepts_branch_password(self):
        branch = SimpleNamespace(
            id=ObjectId(),
            name='DLF',
            city='Chennai',
            staff_login_password_hash=self.branch_password_hash,
        )

        status, payload, login_history = self._login('test@123', branch)

        self.assertEqual(status, 200)
        self.assertEqual(payload['branch']['name'], 'DLF')
        self.assertEqual(
            login_history.call_args.kwargs['login_method'],
            'branch_password',
        )

    def test_configured_branch_does_not_accept_staff_original_password(self):
        branch = SimpleNamespace(
            id=ObjectId(),
            name='EB',
            city='Chennai',
            staff_login_password_hash=self.branch_password_hash,
        )

        status, payload, _ = self._login('existing@456', branch)

        self.assertEqual(status, 401)
        self.assertEqual(payload['error'], 'Invalid password')

    def test_other_branch_keeps_existing_staff_password(self):
        branch = SimpleNamespace(
            id=ObjectId(),
            name='Main Road',
            city='Chennai',
            staff_login_password_hash=None,
        )

        status, payload, login_history = self._login('existing@456', branch)

        self.assertEqual(status, 200)
        self.assertEqual(payload['branch']['name'], 'Main Road')
        self.assertEqual(login_history.call_args.kwargs['login_method'], 'password')

    def test_other_branch_rejects_dlf_eb_shared_password(self):
        branch = SimpleNamespace(
            id=ObjectId(),
            name='Kovur',
            city='Chennai',
            staff_login_password_hash=None,
        )

        status, payload, _ = self._login('test@123', branch)

        self.assertEqual(status, 401)
        self.assertEqual(payload['error'], 'Invalid password')


if __name__ == '__main__':
    unittest.main()
