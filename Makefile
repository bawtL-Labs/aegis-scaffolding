.PHONY: help install install-dev install-gpu test test-cov lint format clean dev server build docs

help: ## Show this help message
	@echo "S.A.M. (Sovereign Autonomous Model) - Development Commands"
	@echo "=========================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

install-gpu: ## Install GPU-enabled dependencies
	pip install -e ".[gpu]"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=sam --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	ruff check sam/
	mypy sam/

format: ## Format code
	black sam/
	isort sam/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

dev: ## Start development server with auto-reload
	uvicorn sam.api:app --reload --host 0.0.0.0 --port 8000

server: ## Start production server
	uvicorn sam.api:app --host 0.0.0.0 --port 8000

build: ## Build package
	python -m build

docs: ## Generate documentation
	# TODO: Add documentation generation when docs are implemented
	@echo "Documentation generation not yet implemented"

# Database management
db-init: ## Initialize database
	python -m sam.memory.maal init

db-migrate: ## Run database migrations
	python -m sam.memory.maal migrate

# S.A.M. specific commands
sam-init: ## Initialize S.A.M. instance
	python -m sam.cli init

sam-start: ## Start S.A.M. instance
	python -m sam.cli start

sam-status: ## Check S.A.M. status
	python -m sam.cli status

# Development utilities
logs: ## Show recent logs
	tail -f logs/sam.log

psp-view: ## View latest PSP
	python -m sam.cli psp show

vsp-dashboard: ## Open V_SP dashboard
	python -m sam.ui.dashboard

# Testing specific scenarios
test-vsp: ## Test V_SP engine
	pytest tests/test_vsp_engine.py -v

test-firewall: ## Test schema firewall
	pytest tests/test_schema_firewall.py -v

test-cdp: ## Test CDP protocol
	pytest tests/test_cdp.py -v

test-schrodinger: ## Test Schrödinger validation
	pytest tests/test_schrodinger.py -v