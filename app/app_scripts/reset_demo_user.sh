#!/bin/sh
# Environment: Inside app
# Function: Reset demo user
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./reset_demo_user.sh
# Ref: JIRA DEV-79

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.reset_demo_user
