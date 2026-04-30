build-db:
	docker compose up -d --build

run:
	python -m src.main

prepare-environment:
	uv sync
	@echo "Remember to activate your venv before running"

access-db:
	docker exec -it acessoria-sql psql -d acessoriadb
