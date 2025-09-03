# Intergalactic Teacher Backend Makefile
.PHONY: help build up down restart logs clean rebuild api-rebuild test lint format migrate shell db-shell redis-cli health-check

# Default target - show help
help:
	@echo "Available commands:"
	@echo "  make build          - Build all Docker containers"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs for all services"
	@echo "  make api-rebuild    - Rebuild and restart API service"
	@echo "  make rebuild        - Rebuild all services from scratch"
	@echo "  make clean          - Stop services and remove containers/volumes"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make migrate        - Run database migrations"
	@echo "  make shell          - Open shell in API container"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make redis-cli      - Open Redis CLI"
	@echo "  make health-check   - Check health of all services"

# Docker Compose Commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

# API specific commands
api-rebuild:
	docker-compose up --build -d api

api-logs:
	docker-compose logs -f api

api-restart:
	docker-compose restart api

# Full rebuild
rebuild: down
	docker-compose build --no-cache
	docker-compose up -d

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f

# Development commands
test:
	docker-compose exec api pytest

test-verbose:
	docker-compose exec api pytest -v

test-coverage:
	docker-compose exec api pytest --cov=app --cov-report=term-missing

lint:
	docker-compose exec api ruff check app/

format:
	docker-compose exec api ruff format app/

# Database commands
migrate:
	docker-compose exec api alembic upgrade head

migration-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec api alembic revision --autogenerate -m "$$msg"

migration-history:
	docker-compose exec api alembic history

migration-rollback:
	docker-compose exec api alembic downgrade -1

# Shell access
shell:
	docker-compose exec api /bin/bash

db-shell:
	docker-compose exec db psql -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-intergalactic_teacher}

redis-cli:
	docker-compose exec redis redis-cli

# Health checks
health-check:
	@echo "Checking API health..."
	@curl -s http://localhost:8000/health | jq '.' || echo "API not responding"
	@echo "\nChecking database connection..."
	@docker-compose exec db pg_isready -U ${POSTGRES_USER:-postgres} || echo "Database not ready"
	@echo "\nChecking Redis connection..."
	@docker-compose exec redis redis-cli ping || echo "Redis not responding"

# Logs for specific services
db-logs:
	docker-compose logs -f db

redis-logs:
	docker-compose logs -f redis

# Development shortcuts
dev: up logs

stop: down

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "Please update .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Docker cleanup
docker-clean:
	docker system prune -af --volumes

# Quick status check
status:
	docker-compose ps

# Run specific Python scripts
run-script:
	@read -p "Enter script path (relative to /app): " script; \
	docker-compose exec api python $$script

# Install new Python packages
pip-install:
	@read -p "Enter package name: " package; \
	docker-compose exec api pip install $$package; \
	docker-compose exec api pip freeze > requirements.txt

# Update requirements
pip-update:
	docker-compose exec api pip freeze > requirements.txt

# Database backup
db-backup:
	@mkdir -p backups
	@docker-compose exec -T db pg_dump -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-intergalactic_teacher} > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created in backups/"

# Database restore
db-restore:
	@read -p "Enter backup file path: " backup; \
	docker-compose exec -T db psql -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-intergalactic_teacher} < $$backup

# Watch logs for errors
watch-errors:
	docker-compose logs -f | grep -E "(ERROR|CRITICAL|Exception|Failed)"