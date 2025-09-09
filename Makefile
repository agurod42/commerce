# Makefile for Wholesale AI Agent

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
PACKAGE_NAME := wholesale_agent

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

.PHONY: help install install-dev setup test lint format type-check clean run setup-db docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

install-rag: ## Install RAG dependencies (large download - PyTorch)
	@echo "$(GREEN)Installing RAG dependencies (this may take a while)...$(NC)"
	$(PIP) install -r requirements-rag.txt

setup: ## Set up development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(YELLOW)Activate the virtual environment with: source $(VENV)/bin/activate$(NC)"
	@echo "$(YELLOW)Then run: make install-dev$(NC)"

setup-db: ## Initialize database and generate mock data
	@echo "$(GREEN)Setting up database...$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main --setup

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	pytest tests/ -v --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest tests/ -v -m "unit" --cov=$(PACKAGE_NAME)

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest tests/ -v -m "integration"

lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	flake8 $(PACKAGE_NAME) tests/
	bandit -r $(PACKAGE_NAME)
	safety check

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	black $(PACKAGE_NAME) tests/ scripts/
	isort $(PACKAGE_NAME) tests/ scripts/

format-check: ## Check code formatting without making changes
	@echo "$(GREEN)Checking code formatting...$(NC)"
	black --check $(PACKAGE_NAME) tests/ scripts/
	isort --check-only $(PACKAGE_NAME) tests/ scripts/

type-check: ## Run type checking
	@echo "$(GREEN)Running type checks...$(NC)"
	mypy $(PACKAGE_NAME)

quality: ## Run all code quality checks
	@echo "$(GREEN)Running all quality checks...$(NC)"
	@make format-check
	@make lint
	@make type-check

clean: ## Clean build artifacts and cache
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete

run: ## Run the wholesale agent CLI
	@echo "$(GREEN)Starting wholesale agent...$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main

run-query: ## Run a single query (usage: make run-query QUERY="your query here")
	@echo "$(GREEN)Running query: $(QUERY)$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main --query "$(QUERY)"

config-check: ## Check system configuration
	@echo "$(GREEN)Checking system configuration...$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main --config-check

migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main --migrate

generate-data: ## Generate mock data
	@echo "$(GREEN)Generating mock data...$(NC)"
	$(PYTHON) -m wholesale_agent.cli.main --generate-data

build: ## Build distribution packages
	@echo "$(GREEN)Building packages...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel

install-package: ## Install package in development mode
	@echo "$(GREEN)Installing package in development mode...$(NC)"
	$(PIP) install -e .

pre-commit: ## Set up pre-commit hooks
	@echo "$(GREEN)Setting up pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit run --all-files

# Docker commands
docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t wholesale-agent:latest .

docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -it --rm \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		wholesale-agent:latest

docker-dev: ## Run Docker container in development mode
	@echo "$(GREEN)Running Docker container in development mode...$(NC)"
	docker run -it --rm \
		-v $(PWD):/app \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		wholesale-agent:latest bash

# Environment setup
env-create: ## Create .env file from template
	@if [ ! -f .env ]; then \
		echo "$(GREEN)Creating .env file from template...$(NC)"; \
		cp .env.template .env; \
		echo "$(YELLOW)Please edit .env file with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

# Database commands
db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f wholesale_agent.db; \
		make setup-db; \
	fi

# Inventory management commands
inventory-add: ## Add stock to product (usage: make inventory-add PRODUCT="USB Cable" QTY=50)
	@echo "$(GREEN)Adding $(QTY) units to $(PRODUCT)...$(NC)"
	$(PYTHON) scripts/manage_inventory.py add "$(PRODUCT)" $(QTY)

inventory-remove: ## Remove stock from product (usage: make inventory-remove PRODUCT="USB Cable" QTY=10)
	@echo "$(GREEN)Removing $(QTY) units from $(PRODUCT)...$(NC)"
	$(PYTHON) scripts/manage_inventory.py remove "$(PRODUCT)" $(QTY)

inventory-create: ## Create new product (usage: make inventory-create SKU=NEW-001 NAME="New Product" etc.)
	@echo "$(GREEN)Creating new product $(SKU)...$(NC)"
	$(PYTHON) scripts/manage_inventory.py create $(SKU) "$(NAME)" "$(CATEGORY)" "$(SUPPLIER)" $(COST) $(WHOLESALE) $(RETAIL)

inventory-movements: ## Show stock movements for product (usage: make inventory-movements PRODUCT="USB Cable")
	@echo "$(GREEN)Stock movements for $(PRODUCT):$(NC)"
	$(PYTHON) scripts/manage_inventory.py movements "$(PRODUCT)"

# Monitoring and logs
logs: ## View application logs
	@echo "$(GREEN)Viewing application logs...$(NC)"
	tail -f logs/wholesale_agent.log

logs-error: ## View error logs
	@echo "$(GREEN)Viewing error logs...$(NC)"
	tail -f logs/wholesale_agent_errors.log

# Development helpers
dev-setup: ## Complete development setup
	@echo "$(GREEN)Setting up complete development environment...$(NC)"
	@make setup
	@echo "$(YELLOW)Please activate virtual environment: source $(VENV)/bin/activate$(NC)"
	@echo "$(YELLOW)Then run: make install-dev && make env-create && make setup-db$(NC)"

ci: ## Run CI pipeline locally
	@echo "$(GREEN)Running CI pipeline...$(NC)"
	@make quality
	@make test
	@make build

# Release commands
release-check: ## Check if ready for release
	@echo "$(GREEN)Checking release readiness...$(NC)"
	@make ci
	@echo "$(GREEN)Release checks completed successfully!$(NC)"

# Show current version
version: ## Show current version
	@python -c "import wholesale_agent; print(wholesale_agent.__version__)"

# Default target
.DEFAULT_GOAL := help