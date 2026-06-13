from fastapi import FastAPI
from app.api.endpoints import prices, balance_sheets, control_panel

app = FastAPI(
    title="Oakland Financial Data Lake Platform API",
    version="1.0.0"
)

app.include_router(prices.router, prefix="/api/v1/prices", tags=["Market Prices"])
app.include_router(balance_sheets.router, prefix="/api/v1/balance-sheets", tags=["Fundamental Balance Sheets"])

app.include_router(control_panel.router, tags=["Administrative Control Panels"])

@app.get("/health", tags=["System Utilities"])
async def health_check():
    return {"status": "healthy", "environment": "docker_desktop"}