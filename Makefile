.PHONY: clean export-env
.ONESHELL:
include .env

# Check operating system, if Microsoft then call $(docker_fn)
ifeq ($(shell uname -r | sed -n 's/.*\( *Microsoft *\).*/\1/ip'),Microsoft)
docker_fn=docker.exe
else
docker_fn=docker
endif

update-pip-lib:
	pip freeze > requirements.txt

# Docker compose:
up:
	docker-compose up -d

down:
	docker-compose down

stop:
	docker-compose stop

start:
	docker-compose start

# Legacy docker commands
run-es:
	$(docker_fn) run \
		-d \
		--rm \
		-v $(DOCKER_ES_VOLUME):/usr/share/elasticsearch/data \
		-p 9200:9200 \
		-p 9300:9300 \
		-e "discovery.type=single-node" \
		docker.elastic.co/elasticsearch/elasticsearch:7.8.0

docker-build:
	docker build -t alpine:latest .

docker-run:
	docker run --name alpine -d -p 8000:5000 --rm -e SECRET_KEY=$(SECRET_KEY) \
		-e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
		-e MAIL_USERNAME=$(MAIL_USERNAME) -e MAIL_PASSWORD=$(MAIL_PASSWORD) \
		--link mysql:dbserver \
		-e DATABASE_URL=mysql+pymysql://$(MYSQL_USERNAME):$(MYSQL_PASSWORD)@dbserver/alpine \
		--link elasticsearch:elasticsearch \
		-e ELASTICSEARCH_URL=$(ELASTICSEARCH_URL) \
		alpine:latest

docker-run-mysql:
	docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
		-e MYSQL_DATABASE=alpine -e MYSQL_USER=$(MYSQL_USERNAME) \
		-e MYSQL_PASSWORD=$(MYSQL_PASSWORD) \
		mysql/mysql-server:8.0.21

docker-run-es:
	docker run --name elasticsearch -d -p 9200:9200 -p 9300:9300 --rm \
    	-e "discovery.type=single-node" \
    	docker.elastic.co/elasticsearch/elasticsearch:7.8.0

docker-stop:
	docker container stop alpine mysql elasticsearch
	docker container rm mysql
