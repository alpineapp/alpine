#!/bin/sh
# Environment: Inside app
# Function: Create collections
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./transform_json_clt_to_db.sh
# Ref: JIRA DEV-

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.transform_json_clt_to_db