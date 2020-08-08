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
COPY alpine.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP alpine.py

RUN chown -R alpine:alpine ./
USER alpine

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]