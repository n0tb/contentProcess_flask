import logging
from datetime import datetime

from traceback import format_exception_only as format_exc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import exists

from project import db

errorLog = logging.getLogger("server.error")
appLog = logging.getLogger("server.app")

class BlacklistToken(db.Model):
    __tabename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, unique=True, nullable=False)
    blacklist_on = db.Column(db.DateTime, default=datetime.now)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            appLog.info(f"token_revoked, token_id={self.id}")
        except Exception as e:
            db.session.rollback()
            errorLog.error(format_exc(type(e), e))
            raise
    
    @classmethod
    def check_blacklist(cls, authToken):
        try:
            return db.session\
                .query(exists().where(cls.token == authToken))\
                .scalar()
        except SQLAlchemyError as e:
            errorLog.error(format_exc(type(e), e))
            raise

    
