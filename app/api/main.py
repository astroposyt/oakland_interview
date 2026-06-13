import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.endpoints import prices, balance_sheets, control_panel
from app.core.scheduler import cron_sync_scheduler

app = FastAPI(
    title="Oakland Financial Data Lake Platform API",
    version="1.0.0"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(cron_sync_scheduler())
    yield
    scheduler_task.cancel()

app.include_router(prices.router, prefix="/api/v1/prices", tags=["Market Prices"])
app.include_router(balance_sheets.router, prefix="/api/v1/balance-sheets", tags=["Fundamental Balance Sheets"])

app.include_router(control_panel.router, tags=["Administrative Control Panels"])

@app.get("/health", tags=["System Utilities"])
async def health_check():
    return {"status": "healthy", "environment": "docker_desktop"}