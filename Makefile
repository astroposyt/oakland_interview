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