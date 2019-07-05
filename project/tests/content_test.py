import os
import unittest

from project import create_app, init_db, db
from project.auth.Token import decodeToken, createAccessToken, createAccessToken
from project.content.models import Content
from project.account.models import Account
from project.utils import Status


class ContentTest(unittest.TestCase):

    def setUp(self):
        os.environ['APP_CONFIG'] = 'project.config.TestConfig'
        self.app = create_app()
        app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
        self.app.config.from_object(app_config)
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        self.app.config['UPLOAD_FOLDER'] = os.path.dirname(__file__)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()

        self.token = self.login()
        self.path_test_file = os.path.dirname(__file__)
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def login(self):
        data = {
            'username': 'buba',
            'password': 'bbb'
        }

        resp = self.client.post("/api/auth/login", json=data)
        return resp.get_json()['access_token']

    def test_get_all_contents_success(self):
        resp = self.client.get("/api/contents", headers=self.headers)

        self.assertEquals(resp.status_code, 200)
        self.assertIsNotNone(resp.get_json())

    def test_create_content_success(self):
        data = {
            'filename': 'content_test.xml',
            'created_at': '2019-05-16'
        }

        resp = self.client.post("/api/contents", json=data,  headers=self.headers)
        resp_data = resp.get_json()

        self.assertEquals(resp.status_code, 201)
        self.assertIsNotNone(resp_data['content_id'])
        self.assertEquals(resp_data['data']['status'], Status.UPLOADING.value)
    
    def test_create_content_invalid_filename(self):
        data = {
            'filename': 'invalid_filename',
            'created_at': '2019-05-16'
        }

        resp = self.client.post("/api/contents", json=data,  headers=self.headers)

        self.assertEquals(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'malformed_request')

    def test_create_content_malformed_req(self):
        data = {
            'filename': 'filename.xml',
        }

        resp = self.client.post("/api/contents", json=data,  headers=self.headers)

        self.assertEquals(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'malformed_request')


    def test_getContent_Success(self):
        resp = self.client.get("/api/contents/uuid1", headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['content_id'], 'uuid1')
    
    def test_getContent_NotFound(self):
        resp = self.client.get("/api/contents/uuid100", headers=self.headers)

        self.assertEqual(resp.status_code, 404)

    def test_updateContent_Success(self):
        data = {
            'filename': 'new_fname.xml',
        }

        resp = self.client.put("/api/contents/uuid1", json=data,  headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['data']['filename'], 'new_fname.xml')
    
    def test_updateContent_MalformedReq(self):
        resp = self.client.put("/api/contents/uuid1",
                               json={},  headers=self.headers)
        
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'malformed_request')

    def test_updateContetnt_NotFound(self):
        data = {
            'filename': 'new_fname.xml',
        }

        resp = self.client.put("/api/contents/uuid100",
                               json=data,  headers=self.headers)

        self.assertEqual(resp.status_code, 404)




    

