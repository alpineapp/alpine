.PHONY: clean export-env
.ONESHELL:
include .env

update-pip-lib:
	pip freeze > requirements.txt

docker-rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d
