.PHONY: help install build test lint format clean dev-setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

build: ## Build Rust extension
	maturin develop --release

test: ## Run tests
	pytest tests/ -v --cov=oxen --cov-report=html --cov-report=term

test-fast: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linting checks
	ruff check oxen/ tests/
	mypy oxen/ --ignore-missing-imports

format: ## Format code
	ruff format oxen/ tests/
	black oxen/ tests/

format-check: ## Check code formatting
	ruff format --check oxen/ tests/
	black --check oxen/ tests/

clean: ## Clean build artifacts
	rm -rf target/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

dev-setup: ## Set up development environment
	python -m venv oxenorm_env
	. oxenorm_env/bin/activate && pip install -e ".[dev]"
	. oxenorm_env/bin/activate && pre-commit install
	. oxenorm_env/bin/activate && maturin develop --release

rust-test: ## Run Rust tests
	cargo test

rust-clippy: ## Run Rust clippy
	cargo clippy -- -D warnings

rust-fmt: ## Format Rust code
	cargo fmt

rust-fmt-check: ## Check Rust code formatting
	cargo fmt -- --check

all-checks: format-check lint rust-fmt-check rust-clippy test ## Run all checks

ci: all-checks ## Run CI checks locally
