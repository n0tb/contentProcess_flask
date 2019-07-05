from .models import Account
from marshmallow import Schema, fields, post_load


def validate_passwd(password):
    return 8 <= len(password) <= 50

class AccountShema(Schema):
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True, validate=validate_passwd)
    new_password = fields.Str(load_only=True, required=True, validate=validate_passwd)
    role = fields.Str(load_only=True, required=True)
    create_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

    @post_load
    def make_person(self, data):
        return Account(**data)
