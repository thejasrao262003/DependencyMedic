.PHONY: up down restart logs test lint format seed-demo install shell

up:
	docker-compose up --build -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

test:
	docker-compose run --rm api_gateway pytest /app/tests -v

lint:
	docker-compose run --rm api_gateway ruff check /app
	cd frontend && npm run lint

format:
	docker-compose run --rm api_gateway ruff format /app

seed-demo:
	docker-compose run --rm api_gateway python /app/scripts/seed_demo.py

install:
	cd frontend && npm install

shell:
	docker-compose run --rm api_gateway /bin/bash

status:
	docker-compose ps
