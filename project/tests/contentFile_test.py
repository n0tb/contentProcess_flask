import os
import unittest

from project import create_app, init_db, db
from project.auth.Token import decodeToken, createAccessToken, createAccessToken
from project.content.models import Content
from project.account.models import Account
from project.utils import Status


class ContentFile_Test(unittest.TestCase):

    def setUp(self):
        os.environ['APP_CONFIG'] = 'project.config.TestConfig'
        self.app = create_app()
        app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
        self.app.config.from_object(app_config)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()

        self.token = self.login()
        self.path_test_file = self.app.config['UPLOAD_FOLDER']
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def login(self):
        data = {
            'username': 'buba',
            'password': 'bbb'
        }

        resp = self.client.post("/api/auth/login", json=data)
        return resp.get_json()['access_token']

    def test_upload_file_success(self):
        with self.app.app_context():
            account = Account.find_by_username('buba')
            content = Content.find_by_content_uuid(account.id, 'uuid2')

        with open(f'{self.path_test_file}/upload_test.xml') as f:
            resp = self.client.put(f"/api/contents/{content.uuid}/file",
                                   headers=self.headers,
                                   data=f)
        with self.app.app_context():
            content = Content.find_by_content_id(
                content.account_id, content.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(content.status, Status.PROCESSING.value)
        self.assertTrue(os.path.isfile(content.path_file))

    def test_upload_file_invalid(self):
        with self.app.app_context():
            account = Account.find_by_username('buba')
            content = Content.find_by_content_uuid(account.id, 'uuid1')

        with open(f'{self.path_test_file}/upload_test.xml') as f:
            resp = self.client.put(f"/api/contents/{content.uuid}/file",
                                   headers=self.headers,
                                   data=f)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'file_alredy_upload')
