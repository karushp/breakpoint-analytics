.PHONY: help install ingest build export clean run-dashboard

help:
	@echo "Tennis Analytics Dashboard - Makefile Commands"
	@echo ""
	@echo "  make install      - Install Python dependencies"
	@echo "  make ingest       - Download and ingest data from Sackmann repo"
	@echo "  make build        - Build features and analytics"
	@echo "  make export       - Export data to JSON for dashboard"
	@echo "  make all          - Run full pipeline (ingest -> build -> export)"
	@echo "  make clean        - Clean generated files"
	@echo "  make run-dashboard - Start local web server for dashboard"

install:
	pip install -r requirements.txt

ingest:
	python pipelines/ingest_sackmann.py

build:
	python pipelines/build_features.py

export:
	python pipelines/export_dashboard_data.py

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
	python -m http.server 8000
