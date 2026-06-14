from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.repositories.bronze_repo import BronzeRepository
from app.repositories.silver_repo import SilverRepository

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")
from app.core.logger import get_logger

logger = get_logger(__name__)

@router.get("/control-panel", response_class=HTMLResponse)
async def render_control_panel(request: Request):
    logger.info("Control panel saved")
    return templates.TemplateResponse(request=request, name="control_panel.html")

@router.get("/data-viewer", response_class=HTMLResponse)
async def render_data_viewer(request: Request):
    """Fetches real-time snapshots of the data platform layers from their respective domain repositories."""

    bronze_rows = await BronzeRepository.fetch_diagnostic_bronze(limit=15)
    silver_prices = await SilverRepository.fetch_diagnostic_silver_prices(limit=15)
    silver_balances = await SilverRepository.fetch_diagnostic_silver_balances(limit=15)

    return templates.TemplateResponse(
        request=request, 
        name="data_viewer.html",
        context={
            "bronze_data": bronze_rows,
            "silver_prices": silver_prices,
            "silver_balances": silver_balances
        }
    )