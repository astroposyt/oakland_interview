from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import api_v1, pages, websockets

from app.core.db import init_db_pool, close_db_pool
from app.core.scheduler import start_scheduler
from app.core.logger import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db_pool()
    start_scheduler()
    yield
    await close_db_pool()

app = FastAPI(
    title="Oakland Financial Data Lake Platform API",
    version="2.0.0", 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(pages.router)
app.include_router(websockets.router)
app.include_router(api_v1.router)

@app.get("/health", tags=["System Utilities"])
async def health_check():
    return {"status": "healthy", "architecture": "layered_srp"}