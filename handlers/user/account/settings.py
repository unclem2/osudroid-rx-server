from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from objects import glob
import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("")
async def settings(request: Request):
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Not logged in"})

    return templates.TemplateResponse(request, "account/settings.html")
