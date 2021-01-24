.PHONY: clean export-env
.ONESHELL:
include .env

update-pip-lib:
	pip freeze > requirements.txt

docker-rebuild:
ifndef ENV
	$(error ENV is undefined. Should be {local, prod})
endif
	docker-compose down
	docker-compose build
	docker-compose up -d

lint:
	flake8 ./app --count --select=E9,F63,F7,F82,F401 --show-source --statistics \
			--extend-ignore=E402
