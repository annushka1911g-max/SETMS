# =============================================================================
# SETMS — Smart Emergency Traffic Management System
# Makefile for SIH demonstration, development, testing, and evaluation
# =============================================================================

.PHONY: all help dev backend frontend ai-engine seed test lint build docker-up docker-down clean

SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn
NPM := npm

help:
	@echo "================================================================="
	@echo "SETMS — Smart Emergency Traffic Management System"
	@echo "================================================================="
	@echo "Available commands:"
	@echo "  make install       Install all Python and Node.js dependencies"
	@echo "  make dev           Start backend and frontend concurrently"
	@echo "  make backend       Run FastAPI backend on http://localhost:8000"
	@echo "  make frontend      Run Vite React frontend on http://localhost:5173"
	@echo "  make ai-engine     Run AI Computer Vision service on http://localhost:8001"
	@echo "  make seed          Seed database with Navapur test city data"
	@echo "  make test          Run automated test suite"
	@echo "  make lint          Check code style and types"
	@echo "  make build         Build frontend production bundle"
	@echo "  make docker-up     Start complete stack via Docker Compose"
	@echo "  make docker-down   Stop Docker Compose containers"
	@echo "  make clean         Remove build artifacts and caches"
	@echo "================================================================="

install:
	@echo "==> Setting up Python virtual environment..."
	@python3 -m venv $(VENV)
	@$(VENV)/bin/pip install --upgrade pip
	@$(VENV)/bin/pip install -r backend/requirements.txt
	@echo "==> Installing frontend dependencies..."
	@cd frontend && $(NPM) install

backend:
	@echo "==> Starting SETMS Backend on port 8000..."
	@cd backend && ../$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	@echo "==> Starting SETMS Frontend on port 5173..."
	@cd frontend && $(NPM) run dev

ai-engine:
	@echo "==> Starting SETMS AI Engine on port 8001..."
	@cd ai-engine && ../$(UVICORN) app.main:app --host 0.0.0.0 --port 8001 --reload

seed:
	@echo "==> Seeding database with Navapur test network..."
	@cd backend && ../$(PYTHON) -m scripts.seed

test:
	@echo "==> Running backend test suite..."
	@cd backend && ../$(PYTEST) tests/ -v
	@echo "==> Running frontend typecheck & build test..."
	@cd frontend && $(NPM) run build

lint:
	@echo "==> Running frontend linter & type check..."
	@cd frontend && npx tsc -b
	@echo "==> Running backend ruff linter..."
	@cd backend && ../$(VENV)/bin/ruff check app tests

build:
	@echo "==> Building frontend bundle..."
	@cd frontend && $(NPM) run build

docker-up:
	@echo "==> Launching SETMS via Docker Compose..."
	@docker compose up -d

docker-down:
	@echo "==> Stopping Docker Compose services..."
	@docker compose down

clean:
	@echo "==> Cleaning cache directories..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@rm -rf frontend/dist
