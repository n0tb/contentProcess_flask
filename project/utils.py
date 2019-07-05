from enum import Enum
from functools import wraps
from flask import request, jsonify, make_response, g
from project.auth.Token import _token_required


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    PROCESSING = 'processing'
    UPLOADING = 'uploading'


def token_required(json=False):
    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                g.token, g.payload = _token_required(
                    request.headers.get("Authorization", None))
                return fn(*args, **kwargs)
            except Exception as e:
                if json:
                    return jsonify(error=str(e)), 401
                return {'error': str(e)}, 401

        return wrapped
    return wrapper


def is_json(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not request.is_json:
            return jsonify(error='Content-Type should be application/json'), 400
        return view(*args, **kwargs)
    return wrapped_view
