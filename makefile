ifeq ($(OS), Windows_NT)
    PYTHON = .venv\Scripts\python
else
    PYTHON = .venv/bin/python
endif

help:
	@echo First, run `make prepare-environment`
	@echo Then, run `make build-db`
	@echo Wait a few seconds, then run `make upgrade-db`
	@echo Now you're ready to run with `make run`

build-db:
	docker compose up -d --build

destroy-db:
	$(PYTHON) -m alembic downgrade base
	docker compose down -v

run:
	$(PYTHON) -m src.main

prepare-environment:
	uv sync
	@echo Remember to activate your venv before running

access-db:
	docker exec -it assessoria-sql psql -d assessoriadb

upgrade-db:
	$(PYTHON) -m alembic upgrade head

downgrade-db:
	$(PYTHON) -m alembic downgrade -1
