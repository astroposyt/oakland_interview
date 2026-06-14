from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")
from app.core.logger import get_logger

logger = get_logger(__name__)

@router.get("/control-panel", response_class=HTMLResponse)
async def render_control_panel(request: Request):
    logger.info("Control panel saved")
    return templates.TemplateResponse(request=request, name="control_panel.html")