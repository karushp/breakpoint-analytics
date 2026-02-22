.PHONY: help install ingest build export clean run-dashboard sync

# Check if uv is installed
UV := $(shell command -v uv 2> /dev/null)

help:
	@echo "Breakpoint Analytics - Makefile Commands"
	@echo ""
	@echo "  make install      - Install Python dependencies with uv"
	@echo "  make sync         - Sync dependencies (uv sync)"
	@echo "  make ingest       - Download and ingest data from Sackmann repo"
	@echo "  make build        - Build features and analytics"
	@echo "  make export       - Export data to JSON for dashboard"
	@echo "  make all          - Run full pipeline (ingest -> build -> export)"
	@echo "  make clean        - Clean generated files"
	@echo "  make run-dashboard - Start local web server for dashboard"

install:
	@if [ -z "$(UV)" ]; then \
		echo "Error: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	uv venv
	uv pip install -r requirements.txt

sync:
	@if [ -z "$(UV)" ]; then \
		echo "Error: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	uv venv
	uv pip install -r requirements.txt
	uv pip install -e .

ingest:
	@if [ ! -d ".venv" ]; then \
		echo "Error: Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	PYTHONPATH=. .venv/bin/python pipelines/ingest_sackmann.py

build:
	@if [ ! -d ".venv" ]; then \
		echo "Error: Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	PYTHONPATH=. .venv/bin/python pipelines/build_features.py

export:
	@if [ ! -d ".venv" ]; then \
		echo "Error: Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	PYTHONPATH=. .venv/bin/python pipelines/export_dashboard_data.py

all: ingest build export
	@echo "Pipeline complete!"

clean:
	rm -rf data/raw/*.csv
	rm -rf data/processed/*.csv
	rm -rf outputs/*.json
	@echo "Cleaned generated files"

run-dashboard:
	@echo "Starting local web server..."
	@echo "Open http://localhost:8000/dashboard/ in your browser"
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m http.server 8000; \
	else \
		python3 -m http.server 8000; \
	fi
