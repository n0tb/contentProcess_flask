import logging
from datetime import datetime
from traceback import format_exception_only as format_exc

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import exists
from werkzeug.security import check_password_hash, generate_password_hash

from project import db
from project.Exceptions import EntityNotFoundError


errorLog = logging.getLogger("server.error")
appLog = logging.getLogger("server.app")


class Account(db.Model):
    __tablename__ = 'account'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    create_at = db.Column(db.DateTime, default=datetime.now)
    modified_at = db.Column(db.DateTime, onupdate=datetime.now)
    deleted = db.Column(db.Boolean, default=False)
    passwdchg = db.Column(db.Boolean, default=False)
    _password = db.Column("password", db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = generate_password_hash(value)

    def check_password(self, value):
        return check_password_hash(self.password, value)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            appLog.info(
                f"account create, accunt_id={self.id}, username={self.username}")
        except SQLAlchemyError as e:
            db.session.rollback()
            errorLog.error(format_exc(type(e), e))
            raise

    def commit(self):
        try:
            appLog.info(
                f"account update, account_id={self.id}")
            db.session.commit()
        except SQLAlchemyError as e:
            db.sessions.rollback()
            errorLog.error(format_exc(type(e), e))
            raise

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            appLog.info(
                f"account deleted, accunt_id={self.id}, username={self.username}")
        except SQLAlchemyError as e:
            db.session.rollback()
            errorLog.error(format_exc(type(e), e))
            raise

    @classmethod
    def get_all(cls):
        try:
            return cls.query.all()
        except SQLAlchemyError as e:
            errorLog.error(format_exc(type(e), e))
            raise

    @classmethod
    def find_by_account_id(cls, account_id):
        try:
            account = cls.query.get(account_id)
            if not account:
                e = EntityNotFoundError(f"account not found, id={account_id}")
                errorLog.error(format_exc(type(e), e))
                raise e
            return account
        except SQLAlchemyError as e:
            errorLog.error(format_exc(type(e), e))
            raise

    @classmethod
    def find_by_username(cls, username):
        try:
            account = cls.query.filter_by(username=username).first()
        except SQLAlchemyError as e:
            errorLog.error(format_exc(type(e), e))
            raise

        if account:
            return account
        else:
            e = EntityNotFoundError(
                f"account not found, username={username}")
            errorLog.error(format_exc(type(e), e))
            raise e

    @classmethod
    def account_exists(cls, username):
        try:
            return db.session\
                .query(exists().where(cls.username == username))\
                .scalar()
        except SQLAlchemyError as e:
            errorLog.error(format_exc(type(e), e))
            raise
