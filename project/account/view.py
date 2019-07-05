import logging
from traceback import format_exception_only as format_exc
from flask import Blueprint, g, request, jsonify
from flask_restful import Api, Resource

from .models import Account
from .schemas import AccountShema
from project.Exceptions import EntityNotFoundError
from project.utils import is_json, token_required


bp = Blueprint('account', __name__, url_prefix='/api')
api = Api(bp)

app_log = logging.getLogger("server.app")
error_log = logging.getLogger("server.error")


@api.resource('/account')
class AccountApi(Resource):

    @token_required()
    def get(self):
        try:
            account = Account.find_by_account_id(g.payload['account_id'])
        except EntityNotFoundError:
            return {}, 404
        except Exception:
            return {}, 500

        schema = AccountShema()
        responseObj = schema.dump(account).data
        return responseObj

    @is_json
    def put(self):
        data = request.json
        try:
            username = data['username']
            password = data['password']
            new_password = data['new_password']
        except KeyError as e:
            error_log.error(format_exc(type(e), e))
            return {"error": "malformed_request"}, 400

        try:
            account = Account.find_by_username(username)
            if not account.check_password(password):
                error_log.error(f"invalid_passwd, username={username}")
                raise EntityNotFoundError

        except EntityNotFoundError:
            return {"error": "invalid_username_or_password"}, 404
        except Exception:
            return {}, 500

        account.password = new_password
        if not account.passwdchg:
            account.passwdchg = True

        try:
            account.commit()
            app_log.info(f'change passwd success, acc_id={account.id}')
            return {}, 200
        except Exception:
            return {}, 500
