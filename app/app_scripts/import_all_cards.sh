#!/bin/sh
# Environment: Inside app
# Function: Migrate next_date and bucket from Card model to LearnSpacedRepetition model
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./import_all_cards.sh
# Ref: JIRA DEV-54

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.import_all_cards
