run:
	python -m src.main

prepare-environment:
	uv sync
	@echo "Remember to activate your venv before running"

access-database:
	docker exec -it acessoria-sql psql -d acessoriadb
