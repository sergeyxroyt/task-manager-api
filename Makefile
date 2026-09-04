COMPOSE_FILE := ./deployments/docker-compose.yaml
COMPOSE_PROJECT_NAME := task-manager

.PHONY: lint format typecheck makemigrations migrate dev-run dev-docker-up \
	dev-docker-down test

lint:
	uv run ruff check .
	uv run ruff format . --check

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

makemigrations:
	uv run python src/manage.py makemigrations

migrate:
	uv run python src/manage.py migrate

dev-run:
	uv run python src/manage.py runserver

dev-docker-up:
	docker compose --env-file .env -f $(COMPOSE_FILE) build
	COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) \
	docker compose --env-file .env -f $(COMPOSE_FILE) up -d

dev-docker-down:
	docker compose --env-file .env -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT_NAME) down

test:
	cd src && uv run python run_tests.py
