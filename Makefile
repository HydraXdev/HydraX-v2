# HydraX v2 Makefile

.PHONY: install dev test clean lint format run deploy help

# Variables
PYTHON = python3
PIP = pip3
VENV = venv
FLASK_APP = src/core/TEN_elite_commands_FULL.py

# Help
help:
	@echo "HydraX v2 Development Commands:"
	@echo "  install    Install dependencies"
	@echo "  dev        Setup development environment"
	@echo "  test       Run tests"
	@echo "  lint       Run linting"
	@echo "  format     Format code"
	@echo "  run        Run the application"
	@echo "  deploy     Deploy application"
	@echo "  clean      Clean build artifacts"

# Installation
install:
	$(PIP) install -r requirements.txt

dev: install
	$(PIP) install -r requirements-dev.txt
	@echo "Development environment ready!"

# Testing
test:
	pytest tests/ -v

# Code Quality
lint:
	flake8 src/ tests/
	@echo "Linting complete!"

format:
	black src/ tests/
	@echo "Code formatted!"

# Running
run:
	FLASK_APP=$(FLASK_APP) flask run --debug

# Deployment
deploy:
	bash deploy_flask.sh

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

# Docker (future)
docker-build:
	docker build -t hydrax-v2 .

docker-run:
	docker run -p 5000:5000 hydrax-v2