from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from handlers.response import success_str

router = APIRouter()
templates = Jinja2Templates(directory="templates")

php_file = True


@router.get("")
async def logout(request: Request):
    response = templates.TemplateResponse(request, "success.html", {"success_message": success_str("Logout successful")})
    response.delete_cookie("login_state")
    return response
