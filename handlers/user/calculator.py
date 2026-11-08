from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("", name="user_calculator")
async def calculator(request: Request):
    return templates.TemplateResponse(request, "calculator.html")
