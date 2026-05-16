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

demo:
	@echo "==> Tearing down and rebuilding..."
	docker-compose down -v
	docker-compose up --build -d
	@echo "==> Waiting for services to be healthy..."
	@sleep 20
	@echo "==> Seeding demo data..."
	docker-compose run --rm api_gateway python /app/scripts/seed_demo.py
	@echo "==> Triggering demo pipeline (CVE-2023-32681 → requests SSRF)..."
	@sleep 2
	curl -s -X POST http://localhost:9000/api/v1/vulnerabilities/vuln-demo-003/match | python3 -m json.tool
	@echo ""
	@echo "✓ Demo pipeline triggered!"
	@echo "  Frontend : http://localhost:9005"
	@echo "  API docs : http://localhost:9000/docs"
	@echo "  Logs     : docker-compose logs -f reachability_analysis remediation_engine gitlab_integration"
