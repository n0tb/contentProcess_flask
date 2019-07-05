import os
import unittest

from project import create_app, init_db, db
from project.auth.Token import createAccessToken, _token_required, extractToken
from project.Exceptions import *
from jwt.exceptions import InvalidTokenError

class TokenTest(unittest.TestCase):

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

    def test_createAccessToken(self):
        access_token = createAccessToken(1, "role")

        self.assertIsNotNone(access_token)

    def test_token_required_valid_token(self):
        token = createAccessToken(1, "role")
        authHeader = f"Baerer {token}"

        with self.app.app_context():
            encoded_token, payload = _token_required(authHeader)

        self.assertEqual(token, encoded_token)
        self.assertEqual(payload['account_id'], 1)
        self.assertEqual(payload['role'], "role")

    def test_token_required_AuthHederNotFound(self):
        with self.app.app_context():
            self.assertRaises(AuthHederNotFound, _token_required, None)

    def test_token_required_TokenNotFoundError(self):
        with self.app.app_context():
            self.assertRaises(TokenNotFoundError, _token_required, "Baerer ")
            self.assertRaises(TokenNotFoundError, _token_required, "Baerer")

    def test_token_required_should_InvalidTokenError(self):
        authHeader = f"Baerer token123"
        
        with self.app.app_context():
            self.assertRaises(InvalidTokenError, _token_required, authHeader)

    def test_token_required_should_RevokedTokenError(self):
        token = createAccessToken(1, "role")
        authHeader = f'Bearer {token}'
        headers = {'Authorization': authHeader}

        resp = self.client.get("/api/auth/logout", headers=headers)
        self.assertEqual(resp.status_code, 200)

        with self.app.app_context():
            self.assertRaises(RevokedTokenError, _token_required, authHeader)
        

    
    

