import logging
import json
from traceback import format_exception_only as format_exc
from flask import Blueprint, g, request, jsonify

from .models import BlacklistToken
from project.account.models import Account
from project.account.schemas import AccountShema
from .Token import createAccessToken
from project.utils import is_json, token_required
from project.Exceptions import EntityNotFoundError


bp = Blueprint('auth', __name__, url_prefix='/api/auth')

app_log = logging.getLogger("server.app")
error_log = logging.getLogger("server.error")


@bp.route('/register', methods=['POST'])
@is_json
@token_required(json=True)
def register():
    if g.payload['role'] != 'admin':
        error_log.error(
            f"register not allowed, acc_id={g.payload['account_id']}, role={g.payload['role']}")
        return jsonify(error='not_allowed'), 403

    schema = AccountShema()
    result = schema.loads(request.data, partial=('new_password',))
    if result.errors:
        return jsonify(error='malformed_request'), 400
    account = result.data

    try:
        if Account.account_exists(account.username):
            error_log.error(
                f"username_already_exists, username={account.username}")
            return jsonify(error="username_already_exists"), 400

        account.save()
        app_log.info(f'register success, acc_id={account.id}')
    except Exception:
        return jsonify(), 500

    responseObj = schema.dump(account)
    return jsonify(responseObj.data)


@bp.route('/login', methods=['POST'])
@is_json
def login():
    data = request.json
    try:
        username = data['username']
        password = data['password']
    except KeyError:
        return jsonify(error="malformed_request"), 400

    try:
        account = Account.find_by_username(username)
    except EntityNotFoundError:
        return jsonify(error="invalid_username_or_password"), 404
    except Exception:
        return jsonify(), 500

    if not account.check_password(password):
        error_log.error(
            f"invalid_username_or_password, username={account.username}")
        return jsonify(error="invalid_username_or_password"), 404
    if not account.passwdchg:
        error_log.error(
            f"not_change_default_password, username={account.username}")
        return jsonify(error="not_change_default_password"), 400

    accessToken = createAccessToken(account.id, account.role)
    app_log.info(f"login, username={account.username}")
    return jsonify(access_token=accessToken)


@bp.route('/logout')
@token_required(json=True)
def logout():
    blackedlistToken = BlacklistToken(token=g.token)
    try:
        blackedlistToken.save()
        app_log.info(f"logout, account_id={g.payload['account_id']}")
        return jsonify(), 200
    except Exception:
        return jsonify(), 500
