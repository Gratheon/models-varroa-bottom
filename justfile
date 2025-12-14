start:
	COMPOSE_PROJECT_NAME=gratheon docker compose up --build

stop:
	COMPOSE_PROJECT_NAME=gratheon docker compose down

run-local:
	python3 server.py

test:
	@echo "Testing server with GET request..."
	@curl -s http://localhost:8750 | head -10

logs:
	docker compose logs -f

