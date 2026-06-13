from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import prices, balance_sheets, control_panel
from app.core.database import init_db_pool, close_db_pool
from app.core.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    
    start_scheduler()
    
    yield

    await close_db_pool()

app = FastAPI(
    title="Oakland Financial Data Lake Platform API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(prices.router, prefix="/api/v1/prices", tags=["Market Prices"])
app.include_router(balance_sheets.router, prefix="/api/v1/balance-sheets", tags=["Fundamental Balance Sheets"])
app.include_router(control_panel.router, tags=["Administrative Control Panels"])

@app.get("/health", tags=["System Utilities"])
async def health_check():
    return {"status": "healthy", "environment": "docker_desktop"}