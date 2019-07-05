import os
import unittest

from project import create_app, init_db, db
from project.auth.Token import decodeToken, createAccessToken
from project.account.models import Account
from project.auth.Token import createAccessToken

class AccountTest(unittest.TestCase):

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
        
        self.token = self.login()

    def login(self):
        data = {
            'username': 'buba',
            'password': 'bbb'
        }

        resp = self.client.post("/api/auth/login", json=data)
        return resp.get_json()['access_token']

    def test_get_account(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        resp = self.client.get("/api/account", headers=headers)
        data = resp.get_json()
        
        self.assertEquals(resp.status_code, 200)
        self.assertEquals('buba', data['username'])
        self.assertEqual('buba@mail.com', data['email'])
        self.assertIsNotNone(data['create_at'])
    
    def test_get_account_accountNotFound(self):
        token = createAccessToken(10, "role")
        headers = {'Authorization': f'Bearer {token}'}

        resp = self.client.get("/api/account", headers=headers)

        self.assertEqual(resp.status_code, 404)

    def test_update_account(self):
        data = {
            'username': 'puba',
            'password': 'ppp',
            'new_password': '123'
        }
        headers = {'Authorization': f'Bearer {self.token}'}

        resp = self.client.put('/api/account', json=data, headers=headers)

        self.assertEqual(resp.status_code, 200)

    def test_update_account_malformed_req(self):
        data = {
            'username': 'puba',
            'password': 'ppp',
        }

        resp = self.client.put('/api/account', json=data)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'malformed_request')
    
    def test_update_account_invalid_username(self):
        data = {
            'username': 'puba1',
            'password': 'ppp',
            'new_password': '123'
        }
        headers = {'Authorization': f'Bearer {self.token}'}

        resp = self.client.put('/api/account', json=data, headers=headers)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()['error'],
                         'invalid_username_or_password')
    
    def test_update_account_invalid_passwd(self):
        data = {
            'username': 'puba',
            'password': 'ppp1',
            'new_password': '123'
        }
        headers = {'Authorization': f'Bearer {self.token}'}

        resp = self.client.put('/api/account', json=data, headers=headers)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()['error'],
                         'invalid_username_or_password')
