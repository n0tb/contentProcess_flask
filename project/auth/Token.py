import os
import jwt
from functools import wraps
from datetime import datetime, timedelta

from flask import request, make_response, jsonify, g

from project import config
from .models import BlacklistToken
from project.Exceptions import *


def _token_required(authHeader):
    encoded_token = extractToken(authHeader)
    payload = decodeToken(encoded_token)
    if tokenRevoked(encoded_token):
        raise RevokedTokenError('access_token_revoked')
    return encoded_token, payload


def tokenRevoked(authToken):
    return bool(BlacklistToken.check_blacklist(authToken))


def encodeToken(expires_delta, account_id, role):
    app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
    config_class = getattr(config, app_config.split('.')[-1])
    
    now = datetime.utcnow()
    payload = {
        'account_id': account_id,
        'role': role,
        'iat': now,
        'exp': now + expires_delta
    }
    return jwt.encode(payload,
                      config_class.SECRET_KEY,
                      algorithm='HS256')\
        .decode('utf-8')


def decodeToken(encodeToken):
    app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
    config_class = getattr(config, app_config.split('.')[-1])

    try:
        return jwt.decode(encodeToken,
                          config_class.SECRET_KEY,
                          algorithms=['HS256'])
    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredSignatureError("expired_signature_error")


def createAccessToken(accountId, role):
    expires_delta = timedelta(hours=3)
    return encodeToken(expires_delta, accountId, role)


def extractToken(authHeader):
    if not authHeader:
        raise AuthHederNotFound('auth_header_not_found')

    try:
        token = authHeader.split(" ")[1]
    except IndexError:
        raise TokenNotFoundError('access_token_not_found')

    if not token:
        raise TokenNotFoundError('access_token_not_found')
    return token

