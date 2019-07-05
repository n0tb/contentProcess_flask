import os
import logging


host = 'http://127.0.0.1'
port = '5000'
config = {
    'MSSQL_CONN_URL': 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=;DATABASE=;UID=;PWD=;',
    'REDIS_CONN_URL': '',
    'REDIS_QUEUE': '',
    'PASSWD': '',
    'PROC': '',
    'ROBOT_PWD': '',
    'ROBOT_USERNAME': '',
    'UPDATE_ENDPOINT': f'{host}:{port}/api/contents',
    'LOGIN_ENDPOINT': f'{host}:{port}/api/auth/login'
}


def configLogger():
    project_dir = os.path.dirname(__file__)
    try:
        os.makedirs(f'{project_dir}/log')
    except FileExistsError:
        pass

    logging.root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - [%(filename)s:%(lineno)s - %(funcName)s()] - %(levelname)s - %(message)s')

    fh = logging.FileHandler(f'{project_dir}/log/robot.log', encoding='utf-8')
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logging.root.addHandler(fh)
    logging.root.addHandler(ch)
