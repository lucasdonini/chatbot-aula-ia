ifeq ($(OS), Windows_NT)
    PYTHON = .venv\Scripts\python
else
    PYTHON = .venv/bin/python
endif

build:
	@echo "Preparing the environment..."
	uv sync
	@echo "Building database..."
	docker compose up -d --build
	@echo "Starting app..."
	$(PYTHON) -m src.main

build-db:
	docker compose up -d --build

run:
	$(PYTHON) -m src.main

prepare-environment:
	uv sync
	@echo "Remember to activate your venv before running"

access-db:
	docker exec -it acessoria-sql psql -d acessoriadb
