import os
import yaml
import logging.config


class Config():
    SECRET_KEY = 'secret'
    JSON_SORT_KEYS = False
    UPLOAD_FOLDER = os.path.dirname(__file__)
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:@127.0.0.1/db'
    REDIS_CONN_URL = 'redis://:path@127.0.0.1:6379/0'
    REDIS_QUEUE = 'queue'
    ROBOT_PWD = 'robot_pwd'
    ADMIN_PWD = 'admin_pwd'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(Config):
    DEVELOPMENT = False
    FLASK_DEBUG = False
    DEBUG = False
    SECRET_KEY = 'secret'
    UPLOAD_FOLDER = os.path.dirname(__file__)


class DevConfig(Config):
    DEVELOPMENT = True
    FLASK_DEBUG = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def config_logging():
    project_dir = os.path.dirname(__file__)
    try:
        os.makedirs(f'{project_dir}/log')
    except FileExistsError as e:
        pass

    absPath = os.path.abspath(f'{project_dir}/logging.yaml')
    with open(absPath, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
