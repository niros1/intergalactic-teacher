.PHONY: help install up down logs clean db-migrate db-reset frontend backend dev status health

# Default target
help:
	@echo "Intergalactic Teacher - Development Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install     - Install all dependencies (frontend + backend)"
	@echo "  up          - Start all services (DB, Redis, API, Frontend)"
	@echo "  down        - Stop all services"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev         - Start development environment"
	@echo "  frontend    - Start frontend development server"
	@echo "  backend     - Start backend API server"
	@echo ""
	@echo "Database Commands:"
	@echo "  db-migrate     - Run database migrations"
	@echo "  db-reset       - Reset database and run migrations"
	@echo "  clean-stories  - Delete all stories & sessions (keeps users/children)"
	@echo ""
	@echo "Utility Commands:"
	@echo "  logs        - Show logs from all services"
	@echo "  status      - Show status of all containers"
	@echo "  health      - Check API health endpoint"
	@echo "  clean       - Stop services and clean up containers"

# Installation
install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

# Main commands
up:
	@echo "Starting all services..."
	cd backend && docker-compose up -d
	@sleep 5
	@echo "Waiting for database to be ready..."
	@make db-migrate
	@echo "All services are up! Use 'make dev' to start frontend."

down:
	@echo "Stopping all services..."
	cd backend && docker-compose down

dev: up
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

# Individual services
frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

backend:
	@echo "Starting backend API server (requires DB to be running)..."
	cd backend && python -m app.main

# Database operations
db-migrate:
	@echo "Running database migrations..."
	cd backend && docker-compose exec -T api alembic upgrade head

db-reset:
	@echo "Resetting database..."
	cd backend && docker-compose down -v
	cd backend && docker-compose up -d intergalactic_db intergalactic_redis
	@sleep 10
	cd backend && docker-compose up -d api
	@sleep 5
	@make db-migrate

clean-stories:
	@echo "Cleaning all stories and related data (preserving users and children)..."
	@docker exec -i intergalactic_db psql -U intergalactic -d intergalactic_teacher < backend/scripts/clean_stories.sql
	@echo "Stories cleanup complete!"

# Utility commands
logs:
	@echo "Showing logs from all services..."
	cd backend && docker-compose logs -f

status:
	@echo "Container status:"
	cd backend && docker-compose ps

health:
	@echo "Checking API health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"

clean:
	@echo "Cleaning up containers and volumes..."
	cd backend && docker-compose down -v --remove-orphans
	@echo "Removing unused Docker images..."
	docker image prune -f

# Build commands
build:
	@echo "Building all services..."
	cd backend && docker-compose build

build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

# Testing commands
test-backend:
	@echo "Running backend tests..."
	cd backend && python -m pytest

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Quick restart
restart: down up