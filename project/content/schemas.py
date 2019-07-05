from os.path import splitext

from .models import Content
from marshmallow import Schema, fields, post_load


class ContentSchema(Schema):
    content_id = fields.Str(attribute="uuid")
    filename = fields.Str(validate=lambda fn: splitext(fn)[
                          1] != '', required=True)
    status = fields.Str()
    total_records = fields.Int()
    success_records = fields.Int()
    error_records = fields.Int()
    created_at = fields.Date(required=True)
    upload_at = fields.DateTime()

    ordered = True

    @post_load
    def make_content(self, data):
        return Content(**data)
