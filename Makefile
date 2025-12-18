.PHONY: help install install-dev test lint format type-check clean run scan

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install package in production mode
	pip install -e .

install-dev: ## Install package with dev dependencies
	pip install -e ".[dev]"
	pre-commit install || echo "pre-commit not installed, skipping"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=arbitrage_bot --cov-report=html --cov-report=term

lint: ## Run linters
	flake8 arbitrage_bot/ tests/
	mypy arbitrage_bot/

format: ## Format code with black
	black arbitrage_bot/ tests/
	isort arbitrage_bot/ tests/

type-check: ## Run type checker
	mypy arbitrage_bot/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the bot (dry-run mode)
	arbitrage-bot run

run-live: ## Run the bot in live mode (WARNING: uses real money!)
	arbitrage-bot run --live

scan: ## Scan markets for opportunities
	arbitrage-bot scan

build: ## Build distribution packages
	python setup.py sdist bdist_wheel

check: format lint type-check test ## Run all checks (format, lint, type-check, test)

ci: install-dev check ## Install dev dependencies and run all checks

