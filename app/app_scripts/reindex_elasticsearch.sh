#!/bin/sh
# Environment: Inside app
# Function: Reindex elasticsearch
# Run command: docker-compose exec -w '/home/alpine/app/app_scripts' alpine ./reindex_elasticsearch.sh

APP_DIR='/home/alpine'

source $APP_DIR/alpine/bin/activate
cd $APP_DIR

python -m app.app_scripts.reindex_elasticsearch