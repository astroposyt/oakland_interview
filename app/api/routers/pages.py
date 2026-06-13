from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/control-panel", response_class=HTMLResponse)
async def render_control_panel(request: Request):
    return templates.TemplateResponse(request=request, name="control_panel.html")