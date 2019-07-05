import os
import click
from flask import Flask, request, make_response, current_app, g
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from werkzeug.datastructures import FileStorage

from project.config import config_logging


db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app_config = os.getenv('APP_CONFIG', 'project.config.DevConfig')
    app.config.from_object(app_config)

    config_logging()

    db.init_app(app)
    app.cli.add_command(init_db_command)

    from project import auth, account, content
    app.register_blueprint(auth.bp)
    app.register_blueprint(account.bp)
    app.register_blueprint(content.bp)

    return app


def init_db():
    db.drop_all()
    db.create_all()

    from project import account
    from project import content

    admin_account = account.Account(username="admin",
                                    password=current_app.config['ADMIN_PWD'],
                                    role="admin",
                                    email="admin@mail.com",
                                    passwdchg=True)

    robot_account = account.Account(username="robot",
                                    password=current_app.config['ROBOT_PWD'],
                                    role="robot",
                                    email="robot@mail.com",
                                    passwdchg=True)

    regular_ready_account = account.Account(username="buba",
                                           password="bbb",
                                           role="user",
                                           email="buba@mail.com",
                                           passwdchg=True)

    regular_account = account.Account(username="puba",
                                      password="ppp",
                                      role="user",
                                      email="puba@mail.com")

    db.session.add(admin_account)
    db.session.add(robot_account)
    db.session.add(regular_ready_account)
    db.session.add(regular_account)
    db.session.commit()

    uploaded_content = content.Content(account_id=regular_ready_account.id,
                                       uuid='uuid1',
                                       filename='test.xml',
                                       filename_fs='test---123.xml',
                                       status='success',
                                       total_records=1500,
                                       success_records=1000,
                                       error_records=500,
                                       path_file=current_app.config['UPLOAD_FOLDER'] + '/test---123.xml',
                                       created_at='2019-05-16')

    created_content = content.Content(account_id=regular_ready_account.id,
                                      uuid='uuid2',
                                      filename='test_upload.xml',
                                      status='uploading',
                                      created_at='2019-05-16')

    db.session.add(uploaded_content)
    db.session.add(created_content)
    db.session.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()
    click.echo("Initialized the database.")
