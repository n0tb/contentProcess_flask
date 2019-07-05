#!/bin/bash

app_dir="/home/app"

export FLASK_APP=$app_dir/app/project
export APP_CONFIG=project.config.ProdConfig

source $app_dir/env/bin/activate
uwsgi run_app.ini