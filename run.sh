#!/bin/sh
source alpine/bin/activate

if [ $ENV == "local" ]
then
    export FLASK_DEBUG=1
    exec flask run -h 0.0.0.0 -p 5000
else
    exec gunicorn --workers=2 --threads=4 --worker-class=gthread \
        --worker-tmp-dir /dev/shm \
        -b :5000 --access-logfile - --error-logfile - alpine:app
fi
