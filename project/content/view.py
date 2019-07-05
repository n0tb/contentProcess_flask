import logging
from datetime import datetime
from traceback import format_exception_only as format_exc

from flask import Blueprint, g, request, jsonify, make_response, current_app
from flask_restful import Api, Resource

from .models import Content
from .schemas import ContentSchema
from project.content.utils import *
from project.utils import is_json, token_required, Status
from project.Exceptions import EntityNotFoundError


bp = Blueprint('content', __name__, url_prefix='/api')
api = Api(bp)
app_log = logging.getLogger("server.app")


@api.resource('/contents')
class Contents(Resource):
    method_decorators = [token_required()]

    def get(self):
        filename = request.args.get('filename', None)
        filename_op = request.args.get('op', None)

        try:
            if filename:
                contents = Content.find_by_filename(
                    g.payload['account_id'], filename, filename_op)
            else:
                contents = Content.get_all(g.payload['account_id'])
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        objects = []
        schema = ContentSchema(exclude=('content_id'))
        for content in contents:
            obj = {
                'content_id': content.uuid,
                'data': schema.dump(content).data,
                'links': {
                    'content': api.url_for(ContentApi, content_uuid=content.uuid),
                    'file': api.url_for(ContentFile, content_uuid=content.uuid)
                }
            }
            objects.append(obj)

        acc_id = g.payload['account_id']
        try:
            responsObj = {
                'total_contents': Content.count_or_count_by_status(acc_id),
                'success_status': Content.count_or_count_by_status(acc_id, 'success'),
                'error_status': Content.count_or_count_by_status(acc_id, 'error'),
                'process_status': Content.count_or_count_by_status(acc_id, 'processing'),
                'uploading_status': Content.count_or_count_by_status(acc_id, 'uploading'),
                'objects': objects
            }
            return responsObj
        except EntityNotFoundError:
            return {}, 404
        except Exception as e:
            return {}, 500

    @is_json
    def post(self):
        schema = ContentSchema()
        result = schema.loads(request.data)
        if result.errors:
            return {'error': 'malformed_request'}, 400
        content = result.data
        content.uuid = get_uuid()
        content.account_id = g.payload['account_id']
        content.status = Status.UPLOADING.value

        try:
            content.save()
        except Exception:
            return {}, 500

        responseObj = {
            'content_id': content.uuid,
            'data': schema.dump(content).data,
            'links': {
                'content': api.url_for(ContentApi, content_uuid=content.uuid),
                'file': api.url_for(ContentFile, content_uuid=content.uuid)
            }
        }
        return responseObj, 201

    @is_json
    def put(self):
        if g.payload['role'] not in ('admin', 'robot'):
            return {}, 403

        data = request.json
        try:
            content = Content.find_by_content_id(
                data['account_id'], data['content_id'])

            content.status = data['status']
            content.total_records = data['total_records']
            content.success_records = data['success_records']
            content.error_records = data['error_records']
            content.commit()
            return {}, 200

        except KeyError:
            return {'error': 'malformed_request'}, 400
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500


@api.resource('/contents/<content_uuid>')
class ContentApi(Resource):
    method_decorators = [token_required()]

    def get(self, content_uuid):
        try:
            content = Content\
                .find_by_content_uuid(g.payload['account_id'], content_uuid)
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        schema = ContentSchema(exclude=('content_id'))
        return {
            'content_id': content_uuid,
            'data': schema.dump(content).data,
            'links': {
                'file': api.url_for(ContentFile, content_uuid=content_uuid)
            }
        }

    @is_json
    def put(self, content_uuid):
        try:
            content = Content.find_by_content_uuid(
                g.payload['account_id'], content_uuid)
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        filename = request.json.get('filename')
        create_at = request.json.get('create_at')
        if filename:
            content.filename = filename
        elif create_at:
            content.create_at = create_at
        else:
            return {'error': 'malformed_request'}, 400

        try:
            content.commit()
        except Exception:
            return {}, 500

        schema = ContentSchema(exclude=('content_id'))
        return {
            'content_id': content_uuid,
            'data': schema.dump(content).data,
            'links': {
                'file': api.url_for(ContentFile, content_uuid=content_uuid)
            }
        }

    def delete(self, content_uuid):
        try:
            content = Content.find_by_content_uuid(
                g.payload['account_id'], content_uuid)

            content.deleted = True
            content.commit()
            return {}, 204
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500


@api.resource('/contents/<content_uuid>/file')
class ContentFile(Resource):
    method_decorators = [token_required()]

    def get(self, content_uuid):
        try:
            content = Content.find_by_content_uuid(
                g.payload['account_id'], content_uuid)
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        if content.status == Status.PROCESSING.value:
            return {'error': 'file_processing'}, 400
        elif content.status == Status.UPLOADING.value:
            return {"error": "file_not_upload"}, 400

        try:
            data = readFile(content.path_file)
        except Exception:
            return {}, 500

        response = make_response(data)
        response.headers['Content-type'] = 'application/xml'
        return response

    def put(self, content_uuid):
        try:
            content = Content.find_by_content_uuid(
                g.payload['account_id'], content_uuid)
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        if content.status not in (Status.UPLOADING.value):
            return {"error": "file_alredy_upload"}, 400

        try:
            content.path_file, content.filename_fs = saveFile(request.stream,
                                                              content.filename,
                                                              current_app.config['UPLOAD_FOLDER'])

            enqueue(content)

            content.status = Status.PROCESSING.value
            content.upload_at = datetime.now()
            content.commit()

            app_log.info(
                f"""file_upload, content_id={content.id},
                fname={content.filename}, fname_in_fs={content.filename_fs}""")
            return {}, 200
        except Exception as e:
            return {}, 500
