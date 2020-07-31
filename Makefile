.PHONY: clean
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

run-es:
	$(docker_fn) run \
		-d \
		--rm \
		-v $(DOCKER_ES_VOLUME):/usr/share/elasticsearch/data \
		-p 9200:9200 \
		-p 9300:9300 \
		-e "discovery.type=single-node" \
		docker.elastic.co/elasticsearch/elasticsearch:7.8.0
