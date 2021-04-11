FROM python:3.8-alpine
# RUN apk add --no-cache --update python3-dev gcc build-base \
#     libressl-dev musl-dev libffi-dev

RUN apk add --no-cache --update python3-dev gcc build-base \
    musl-dev postgresql-dev libffi-dev

RUN adduser -D alpine

WORKDIR /home/alpine

COPY requirements.txt requirements.txt
RUN python -m venv alpine
RUN alpine/bin/pip install -r requirements.txt
RUN alpine/bin/pip install gunicorn psycopg2

COPY app app
COPY migrations migrations
COPY alpine.py config.py boot.sh work.sh run.sh ./
# Create persistent volume to be able to change permission
# https://github.com/docker/compose/issues/3270#issuecomment-363478501
RUN mkdir ./data
RUN chmod +x boot.sh work.sh run.sh
RUN chmod -R +x app/app_scripts/

ENV FLASK_APP alpine.py

USER alpine

EXPOSE 5000
# Run boot.sh in docker-compose command to let worker use the image
# ENTRYPOINT ["./boot.sh"]
