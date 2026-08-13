help:
	@echo 'First, run `make prepare-environment` and create .env.app/.env.compose from their examples'
	@echo 'Then, run `make build-db`'
	@echo 'Wait a few seconds, then run `make upgrade-db`'
	@echo 'Now you are ready to run with `make run`'

build-db:
	docker compose up -d --build

destroy-db:
	uv run python -m alembic downgrade base
	docker compose down -v

run:
	uv run python -m src.main

prepare-environment:
	uv sync
	@echo 'Copy .env.app.example to .env.app and .env.compose.example to .env.compose'

access-db:
	docker exec -it assessoria-sql psql -d assessoriadb

upgrade-db:
	uv run python -m alembic upgrade head

downgrade-db:
	uv run python -m alembic downgrade -1
