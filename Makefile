.PHONY: start stop clean

# The command you wanted!
start:
	@echo "🚀 Spinning up the Database and Backend App simultaneously..."
	docker compose up --build -d
	@echo "✨ System is fully operational!"
	@echo "🖥️  Frontend/API running at: http://localhost:8000"

stop:
	@echo "🛑 Shutting down containers..."
	docker compose down

clean:
	@echo "🧹 Wiping container state and volumes (Fresh Start)..."
	docker compose down -v

init-db:
	docker exec -i postgres psql -U postgres -d my_stock_db < init.sql

test:
	docker compose exec api-server pytest -vv

test-unit:
	docker compose exec api-server pytest tests/unit -vv

test-integration:
	docker compose exec api-server pytest tests/integration -vv

coverage:
	docker compose exec api-server pytest --cov=app tests/unit/ -vv