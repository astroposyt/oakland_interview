from fastapi import FastAPI
from app.api.endpoints import prices, balance_sheets

app = FastAPI(title="Oakland Stock Pipeline")

app.include_router(prices.router)
app.include_router(balance_sheets.router)

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Pipeline plumbing is operational!"}