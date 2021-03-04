#!/bin/sh
# Environment: Inside app
# Function: Export all cards of every user
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./export_all_cards.sh

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.export_all_cards
