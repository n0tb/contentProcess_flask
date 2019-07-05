import os
import json
import uuid
import logging
import redis
from traceback import format_exception_only as format_exc

from flask import g
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from project import config

app_log = logging.getLogger("server.app")
error_log = logging.getLogger("error.log")


def get_uuid():
    return str(uuid.uuid4())[-10:]


def readFile(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:
        error_log.error(format_exc(type(e), e))
        raise


def saveFile(stream, filename, path_conf):
    random_seq = str(uuid.uuid4())[:8]

    full_filename = secure_filename(filename)
    filename, file_extension = os.path.splitext(full_filename)
    filenameFs = f'{filename}---{random_seq}{file_extension}'
    pathFile = os.path.join(path_conf, filenameFs)
    absPath = os.path.abspath(pathFile)

    try:
        FileStorage(stream).save(absPath)
        app_log.info(
            f'file success save, filename={full_filename}, filenameFs={filenameFs}')
        return absPath, filenameFs
    except Exception as e:
        error_log.error(format_exc(type(e), e))
        raise


def get_redis():
    app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
    config_class = getattr(config, app_config.split('.')[-1])

    if 'redis' not in g:
        g.redis_db = redis.Redis.from_url(config_class.REDIS_CONN_URL)
        g.redis_db.ping()
        app_log.info("connect to redis success")
    return g.redis_db


def enqueue(content):
    app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
    config_class = getattr(config, app_config.split('.')[-1])

    data = {
        'account_id': content.account_id,
        'content_id': content.id,
        'content_uuid': content.uuid,
        'file': content.filename_fs
    }

    try:
        conn = get_redis()
        conn.rpush(config_class.REDIS_QUEUE, json.dumps(data))
        app_log.info(f'task enqueue in redis queue, data={data}')
    except redis.RedisError as e:
        error_log.critical(
            f"error connect to redis, error={format_exc(type(e), e)}")
        raise
