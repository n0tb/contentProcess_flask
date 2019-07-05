import unittest
import os

from project import create_app, init_db, db
from project.auth.Token import decodeToken, createAccessToken
from project.account.models import Account


class AuthTest(unittest.TestCase):

    def setUp(self):
        os.environ['APP_CONFIG'] = 'project.config.TestConfig'
        self.app = create_app()
        app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
        self.app.config.from_object(app_config)
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
        print('setUp test')


    def test_register_success(self):
        token = createAccessToken(1, 'admin')
        headers = {'Authorization': f'Bearer {token}'}
        data = {
            'username': 'user',
            'password': 'uuu12345',
            'email': 'user@mail.com',
            'role': 'user'
        }

        resp = self.client.post("/api/auth/register",
                                json=data, headers=headers)
        resp_data = resp.get_json()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_data['username'], "user")


    def test_register_invalid_role(self):
        token = createAccessToken(1, 'user')
        headers = {'Authorization': f'Bearer {token}'}
        data = {
            'username': 'user',
            'password': 'uuu',
            'email': 'user@mail.com',
            'role': 'user'
        }

        resp = self.client.post("/api/auth/register",
                                json=data, headers=headers)
        resp_data = resp.get_json()

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp_data['error'], 'not_allowed')

    def test_register_malformed_request(self):
        token = createAccessToken(1, 'admin')
        headers = {'Authorization': f'Bearer {token}'}
        data = {
            'username': 'user',
            'password': 'uuu',
        }

        resp = self.client.post("/api/auth/register",
                                json=data, headers=headers)
        resp_data = resp.get_json()

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp_data['error'], 'malformed_request')

    def test_register_user_already_exista(self):
        token = createAccessToken(1, 'admin')
        headers = {'Authorization': f'Bearer {token}'}
        data = {
            'username': 'buba',
            'password': 'bbb12345',
            'email': 'user@mail.com',
            'role': 'user'
        }

        resp = self.client.post("/api/auth/register",
                                json=data, headers=headers)
        resp_data = resp.get_json()

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp_data['error'], "username_already_exists")

    def test_login_success(self):
        data = {
            'username': 'buba',
            'password': 'bbb'
        }

        resp = self.client.post("/api/auth/login", json=data)
        token = resp.get_json()['access_token']
        payload = decodeToken(token)

        self.assertIsNotNone(payload)
        self.assertEqual(resp.status_code, 200)

    def test_login_uncorrect_username(self):
        data = {
            'username': 'buba123',
            'password': 'bbb'
        }
        resp = self.client.post("/api/auth/login", json=data)
        token = resp.get_json().get('access_token')
        error = resp.get_json().get('error')

        self.assertIsNone(token)
        self.assertIn('invalid_username_or_password', error)
        self.assertEqual(resp.status_code, 404)

    def test_login_uncorrect_passwd(self):
        data = {
            'username': 'buba',
            'password': '123'
        }

        resp = self.client.post("/api/auth/login", json=data)
        token = resp.get_json().get('access_token')
        error = resp.get_json().get('error')

        self.assertIsNone(token)
        self.assertIn('invalid_username_or_password', error)
        self.assertEqual(resp.status_code, 404)

    def test_login_uncorrect_unchange_passwd(self):
        data = {
            'username': 'puba',
            'password': 'ppp'
        }

        resp = self.client.post("/api/auth/login", json=data)
        token = resp.get_json().get('access_token')
        error = resp.get_json().get('error')

        self.assertIsNone(token)
        self.assertIn('not_change_default_password', error)
        self.assertEqual(resp.status_code, 400)

    def test_login_uncorrect_malformed_body(self):
        data = {
            'username': 'buba',
        }

        resp = self.client.post("/api/auth/login", json=data)
        token = resp.get_json().get('access_token')
        error = resp.get_json().get('error')

        self.assertIsNone(token)
        self.assertIn('malformed_request', error)
        self.assertEqual(resp.status_code, 400)

    def test_logout_success(self):
        with self.app.app_context():
            account = Account.find_by_username('buba')
        token = createAccessToken(account.id, account.role)
        headers = {'Authorization': f'Bearer {token}'}

        resp = self.client.get("/api/auth/logout", headers=headers)

        self.assertEqual(resp.status_code, 200)

    def test_logout_uncorrect_token(self):
        with self.app.app_context():
            account = Account.find_by_username('buba')
        token = createAccessToken(account.id, account.role)[1:10]
        headers = {'Authorization': f'Bearer {token}'}

        resp = self.client.get("/api/auth/logout", headers=headers)

        self.assertEqual(resp.status_code, 401)

    def test_logout_missing_token(self):
        resp = self.client.get("/api/auth/logout")

        self.assertEqual(resp.status_code, 401)
