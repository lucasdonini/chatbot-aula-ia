run:
	python -m src.main

prepare-environment:
	uv sync
	@echo "Remember to activate your venv before running"
