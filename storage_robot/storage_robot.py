import os
import sys
import time
import json
import logging
import pyodbc
import redis
import requests
from enum import Enum
from functools import wraps

from requests.exceptions import RequestException, ConnectionError, ConnectTimeout, HTTPError
from redis.exceptions import RedisError

from config import config, configLogger
from utils import retry


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    PROCESSING = 'processing'
    UPLOADING = 'uploading'


class RedisTaskQueue:
    def __init__(self, conn_url, nameQueue):
        self.conn_url = conn_url
        self.name_queue = nameQueue
        self.conn = None

    def getConn(self):
        try:
            redis_conn = redis.Redis().from_url(self.conn_url)
            redis_conn.ping()
            logger.info("connect to Redis server")
            return redis_conn
        except redis.ConnectionError as e:
            logger.critical(f"Redis server is not running, error={e}")
            raise
    
    def dequeueTask(self):
        if self.conn is None:
            self.conn = self.getConn()
        
        tries, i = 3, 0
        while True:
            try:
                logger.info('robot wait task...')
                task = self.conn.blpop(self.name_queue, 30)
                logger.info(f'robot pop task: {task}')
            except RedisError as e:
                if i < tries - 1:
                    logger.error(f'robot pop error, attempt={i+1}, error={e}')
                    time.sleep(10)
                    i += 1
                    continue
                else:
                    logger.critical(f'robot pop error, all attempt, error={e}')
                    raise

            if not task:
                logger.info(f'robot pop timeout, sleep...')
                time.sleep(30)
                continue

            return json.loads(task[1])

    def enqueueTask(self, conn):
        data = {
            'account_id': 2,
            'content_id': 5,
            'content_uuid': 'qwe123',
            'file': 'test.xml'
        }

        try:
            conn.rpush(self.name_queue, json.dumps(data))
        except Exception as e:
            raise


class HttpClient():
    def __init__(self, **kwargs):
        self.robotUsername = kwargs['ROBOT_USERNAME']
        self.robotPwd = kwargs['ROBOT_PWD']
        self.loginEndpoint = kwargs['LOGIN_ENDPOINT']
        self.updateEndpoint = kwargs['UPDATE_ENDPOINT']
        self.token = None

    def updateContent(self, data, results_proc):
        if self.token is None:
            self.token = self.login()

        headers = { 'Authorization': f'Bearer {self.token}' }
        respData, acc_id, cont_id = self.formRespData(data, results_proc)

        for attempt in range(2):
            try:
                resp = self.make_request('PUT', self.updateEndpoint, respData, headers=headers)
                logger.info(
                    f'content_update success, cont_id={cont_id}, acc_id={acc_id}')
                return resp.status_code

            except HTTPError as e:
                error_msg = e.response.json().get('error')
                
                httpStatus = e.response.status_code
                if httpStatus == 401 and attempt < 1:
                    logger.error(f'''content_update error attempt relogin, http_status={httpStatus}, 
                                http_err_msg={error_msg}, cont_id={cont_id}, acc_id={acc_id}, error={e}''')
                    self.token = self.login()
                    headers['Authorization'] = f'Bearer {self.token}'
                    logger.info(
                        f'relogin success, cont_id={cont_id}, acc_id={acc_id}')
                    continue
                else:
                    logger.error(f'''content_update failed, http_status={httpStatus},
                                http_err_msg={error_msg}, cont_id={cont_id}, acc_id={acc_id}, error={e}''')
                    raise
            except Exception as e:
                logger.error(f'''content_update failed,
                            cont_id={cont_id}, acc_id={acc_id}, error={e}''')
                raise

    def login(self):
        data = {
            'username': self.robotUsername,
            'password': self.robotPwd
        }

        try:
            resp = self.make_request('POST', self.loginEndpoint, data)
            logger.info('robot login success')
            return resp.json()['access_token']
        except Exception as e:
            logger.error(f'login faild, error={e}')
            raise

    @retry((ConnectionError, ConnectTimeout, HTTPError))
    def make_request(self, httpMethod, url, data, headers=None):
        resp = requests.request(httpMethod, url, json=data, headers=headers)
        resp.raise_for_status()
        return resp

    def formRespData(self, data, result_proc):
        acc_id = data['account_id']
        cont_id = data['content_id']
        respData = {
            'account_id': acc_id,
            'content_id': cont_id
        }

        if results_proc.get('status') == 'success':
            respData.update({
                'status': Status.SUCCESS.value,
                'total_records': results_proc['total_records'],
                'success_records': results_proc['success_records'],
                'error_records': results_proc['error_records']
            })
        else:
            respData.update({'status': Status.ERROR.value})

        return respData, acc_id, cont_id



def callProc(filename):
    conn = pyodbc.connect(config['MSSQL_CONN_URL'])
    cursor = conn.cursor()
    # cmd = "{CALL %s } (?)" % (Config.PROC)
    try:
        logger.info(f'proc begin, file={filename}')
        cursor.execute("{CALL store_exp2 (?)}", filename)
        total, success, error = cursor.fetchall()[0]
        logger.info(f'proc call success, file={filename}')
        return {
            'status': 'success',
            'total_records': total,
            'success_records': success,
            'error_records': error
        }

    except pyodbc.DatabaseError as e:
        cursor.rollback()
        logger.error(f'call_proc_error, file={filename}, error={e}')
        return {
            'status': 'error'
        }

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    configLogger()    
    logger = logging.getLogger('storage_robot')
    logger.info("robot on")
    
    taskQueue = RedisTaskQueue(config['REDIS_CONN_URL'], config['REDIS_QUEUE'])
    httpClient = HttpClient(**config)

    try:
        while True:
            data = taskQueue.dequeueTask()
            results_proc = callProc(data['file'])
            httpClient.updateContent(data, results_proc)
    except KeyboardInterrupt:
        logger.info('robot off')
        sys.exit()
    except Exception as e:
        logger.critical(f'robot off, error={e}')
        sys.exit()
    
