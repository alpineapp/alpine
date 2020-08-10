#!/bin/sh
source alpine/bin/activate

exec gunicorn --workers=2 --threads=4 --worker-class=gthread \
    --worker-tmp-dir /dev/shm \
    -b :5000 --access-logfile - --error-logfile - alpine:app
