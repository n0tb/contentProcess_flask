import uuid
import logging
from traceback import format_exception_only as format_exc
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from project import db
from project.account.models import Account
from project.Exceptions import EntityNotFoundError


error_log = logging.getLogger("server.error")
app_log = logging.getLogger("server.app")


class Content(db.Model):
    __tablename__ = 'content'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True,
                     nullable=False)
    account_id = db.Column(db.ForeignKey(Account.id), nullable=False)

    filename = db.Column(db.String, nullable=False)
    filename_fs = db.Column(db.String)
    status = db.Column(db.String)
    total_records = db.Column(db.Integer)
    success_records = db.Column(db.Integer)
    error_records = db.Column(db.Integer)
    deleted = db.Column(db.Boolean, default=False)
    path_file = db.Column(db.String)

    created_at = db.Column(db.Date)
    upload_at = db.Column(db.DateTime)
    modified_at = db.Column(db.DateTime, onupdate=datetime.now)

    account = db.relationship(Account, lazy="select")

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            app_log.info(
                f"create content, content_id={self.id}, content_uuid={self.uuid}")
        except SQLAlchemyError as e:
            db.session.rollback()
            error_log.error(format_exc(type(e), e))
            raise

    def commit(self):
        try:
            db.session.commit()
            app_log.info(
                f"content update, content_id={self.id}, content_uuid={self.uuid}")
        except SQLAlchemyError as e:
            db.sessions.rollback()
            error_log.error(format_exc(type(e), e))
            raise

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            app_log.info(
                f"content delete, content_id={self.id}, content_uuid={self.uuid}")
        except SQLAlchemyError as e:
            db.session.rollback()
            error_log.error(format_exc(type(e), e))
            raise

    @classmethod
    def get_all(cls, acc_id):
        try:
            contents = cls.query\
                .filter_by(account_id=acc_id, deleted=False).all()
        except SQLAlchemyError as e:
            error_log.error(format_exc(type(e), e))
            raise

        if contents:
            return contents
        else:
            e = EntityNotFoundError(
                f"content not found, account_id={acc_id}")
            error_log.error(format_exc(type(e), e))
            raise e

    @classmethod
    def find_by_content_id(cls, acc_id, content_id):
        try:
            content = cls.query\
                .filter_by(id=content_id, account_id=acc_id)\
                .first()
        except SQLAlchemyError as e:
            error_log.error(format_exc(type(e), e))
            raise

        if content:
            return content
        else:
            e = EntityNotFoundError(f"content not found, account_id={acc_id},\
                                    content_uuid={content_id}")
            error_log.error(format_exc(type(e), e))
            raise e

    @classmethod
    def find_by_content_uuid(cls, acc_id, content_uuid):
        try:
            content = cls.query\
                .filter_by(uuid=content_uuid, account_id=acc_id)\
                .first()
        except SQLAlchemyError as e:
            error_log.error(format_exc(type(e), e))
            raise

        if content:
            return content
        else:
            e = EntityNotFoundError(f"content not found, account_id={acc_id},\
                                    content_uuid={content_uuid}")
            error_log.error(format_exc(type(e), e))
            raise e

    @classmethod
    def find_by_filename(cls, acc_id, filename, filename_op=None):
        result_query = cls.query.filter(
            Content.account_id == acc_id, Content.deleted == False)
        if filename_op == 'like':
            print('in like')
            result_query = result_query\
                .filter(Content.filename.like(f'%{filename}%'))
        else:
            result_query = result_query.filter(Content.filename == filename)

        try:
            content = result_query.all()
        except SQLAlchemyError as e:
            error_log.error(format_exc(type(e), e))
            raise

        if content:
            return content
        else:
            e = EntityNotFoundError(
                f"content not found by filename={filename}, account_id={acc_id}")
            error_log.error(format_exc(type(e), e))
            raise e

    @classmethod
    def count_or_count_by_status(cls, acc_id, status=None):
        result_query = cls.query.filter_by(account_id=acc_id, deleted=False)
        if status:
            result_query = result_query.filter_by(status=status)

        try:
            count = result_query.count()
        except SQLAlchemyError as e:
            error_log.error(format_exc(type(e), e))
            raise

        return count if count else 0

    def __repr__(self):
        return f'<Content filename={self.filename}>'
