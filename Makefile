# OMS Trading - Development Makefile
# Usage: make <target>

.PHONY: help install dev-install test lint format clean docker-up docker-down migrate shell

# Default target
.DEFAULT_GOAL := help

# Python and Django settings
PYTHON := python3.11
PIP := pip
DJANGO_SETTINGS_MODULE := backend.apps.core.settings.dev
MANAGE := $(PYTHON) backend/manage.py

# Docker settings
COMPOSE := docker compose
COMPOSE_FILE := docker-compose.yml

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)OMS Trading - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(install|setup)"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(dev|run|shell|migrate)"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(test|lint|format|check)"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "docker"
	@echo ""
	@echo "$(GREEN)Database Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(db|migrate|seed)"

# Setup Commands
install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install -e .

dev-install: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	pre-commit install

setup-env: ## Copy .env.example to .env if not exists
	@if [ ! -f .env ]; then \
		echo "$(GREEN)Creating .env file from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)Please edit .env file with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

# Development Commands
dev: setup-env ## Start development server
	@echo "$(GREEN)Starting development server...$(NC)"
	$(MANAGE) runserver 0.0.0.0:8000

dev-worker: ## Start Celery worker in development
	@echo "$(GREEN)Starting Celery worker...$(NC)"
	cd backend && celery -A apps.core worker --loglevel=info --concurrency=4

dev-beat: ## Start Celery beat scheduler in development
	@echo "$(GREEN)Starting Celery beat...$(NC)"
	cd backend && celery -A apps.core beat --loglevel=info

dev-flower: ## Start Flower for Celery monitoring
	@echo "$(GREEN)Starting Flower...$(NC)"
	cd backend && celery -A apps.core flower --port=5555

shell: ## Start Django shell
	@echo "$(GREEN)Starting Django shell...$(NC)"
	$(MANAGE) shell_plus

# Database Commands
migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(MANAGE) migrate

makemigrations: ## Create new database migrations
	@echo "$(GREEN)Creating database migrations...$(NC)"
	$(MANAGE) makemigrations

migrate-check: ## Check for unapplied migrations
	@echo "$(GREEN)Checking for unapplied migrations...$(NC)"
	$(MANAGE) showmigrations --plan

db-reset: ## Reset database (WARNING: Destroys all data)
	@echo "$(RED)WARNING: This will destroy all database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MANAGE) flush --noinput; \
		echo "$(GREEN)Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

seed-data: ## Load sample data for development
	@echo "$(GREEN)Loading sample data...$(NC)"
	$(MANAGE) loaddata backend/infra/fixtures/sample_data.json

# Code Quality Commands
test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	pytest

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest -m "unit"

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest -m "integration"

test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	pytest --cov --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	pytest --looponfail

lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	ruff check backend/
	mypy backend/

lint-fix: ## Fix linting issues automatically
	@echo "$(GREEN)Fixing linting issues...$(NC)"
	ruff check --fix backend/

format: ## Format code with black and ruff
	@echo "$(GREEN)Formatting code...$(NC)"
	black backend/
	ruff format backend/

format-check: ## Check code formatting without making changes
	@echo "$(GREEN)Checking code formatting...$(NC)"
	black --check backend/
	ruff format --check backend/

check-all: format-check lint test ## Run all code quality checks

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(GREEN)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

# Docker Commands
docker-build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(COMPOSE) build --no-cache web celery-worker celery-beat flower ib-gateway

docker-up: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting all services...$(NC)"
	$(COMPOSE) up -d

docker-down: ## Stop all services
	@echo "$(GREEN)Stopping all services...$(NC)"
	$(COMPOSE) down

docker-logs: ## View logs from all services
	@echo "$(GREEN)Viewing logs...$(NC)"
	$(COMPOSE) logs -f

docker-logs-web: ## View logs from web service only
	@echo "$(GREEN)Viewing web service logs...$(NC)"
	$(COMPOSE) logs -f web

docker-restart: ## Restart all services
	@echo "$(GREEN)Restarting all services...$(NC)"
	$(COMPOSE) restart

docker-clean: ## Remove all containers, networks, and volumes
	@echo "$(RED)WARNING: This will remove all containers, networks, and volumes!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v --remove-orphans; \
		docker system prune -f; \
		echo "$(GREEN)Docker cleanup complete$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

docker-shell: ## Access shell in web container
	@echo "$(GREEN)Accessing web container shell...$(NC)"
	$(COMPOSE) exec web bash

docker-migrate: ## Run migrations in Docker container
	@echo "$(GREEN)Running migrations in Docker...$(NC)"
	$(COMPOSE) exec web python manage.py migrate

# Production Commands
prod-check: ## Check production readiness
	@echo "$(GREEN)Checking production readiness...$(NC)"
	$(MANAGE) check --deploy --settings=backend.apps.core.settings.prod

prod-collect-static: ## Collect static files for production
	@echo "$(GREEN)Collecting static files...$(NC)"
	$(MANAGE) collectstatic --noinput --settings=backend.apps.core.settings.prod

# Utility Commands
clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

superuser: ## Create Django superuser
	@echo "$(GREEN)Creating Django superuser...$(NC)"
	$(MANAGE) createsuperuser

backup-db: ## Backup database to file
	@echo "$(GREEN)Backing up database...$(NC)"
	$(MANAGE) dbbackup

restore-db: ## Restore database from backup
	@echo "$(GREEN)Restoring database...$(NC)"
	$(MANAGE) dbrestore

logs: ## Show Django application logs
	@echo "$(GREEN)Showing application logs...$(NC)"
	tail -f logs/django.log

requirements: ## Generate requirements.txt from pyproject.toml
	@echo "$(GREEN)Generating requirements files...$(NC)"
	pip-compile pyproject.toml --output-file requirements/base.txt
	pip-compile pyproject.toml --extra dev --output-file requirements/dev.txt
	pip-compile pyproject.toml --extra prod --output-file requirements/prod.txt

# Health checks
health: ## Check application health
	@echo "$(GREEN)Checking application health...$(NC)"
	curl -f http://localhost:8000/api/v1/health || echo "$(RED)Application is not healthy$(NC)"

# Performance testing
load-test: ## Run load tests (requires locust)
	@echo "$(GREEN)Running load tests...$(NC)"
	locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Security checks
security-check: ## Run security checks
	@echo "$(GREEN)Running security checks...$(NC)"
	bandit -r backend/ -f json -o security-report.json
	safety check

# Documentation
docs-build: ## Build documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	cd docs && make html

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	cd docs/_build/html && python -m http.server 8080
