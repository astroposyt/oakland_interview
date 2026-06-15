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

restart:
	docker compose restart api-server

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


cli-add:
	docker compose exec api-server python -m app.cli.main add --ticker $(t) --name "$(n)"

cli-sync:
	docker compose exec api-server python -m app.cli.main sync

cli-gold-prices:
	docker compose exec api-server python -m app.cli.main gold --type prices

cli-untrack:
	docker compose exec api-server python -m app.cli.main untrack --ticker $(t)

cli-max-day:
	docker compose exec api-server python -m app.cli.main max-day $(if $(t),--ticker $(t),)