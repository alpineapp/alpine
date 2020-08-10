#!/bin/sh
source alpine/bin/activate

rq worker alpine-tasks -u $REDIS_URL