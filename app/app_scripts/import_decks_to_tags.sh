#!/bin/sh
# Environment: Inside app
# Function: Migrate decks to tags
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./import_decks_to_tags.sh
# Ref: JIRA DEV-64

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.import_decks_to_tags
