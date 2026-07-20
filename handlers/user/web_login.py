from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from handlers.response import success_str
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.api_route("", methods=["GET", "POST"])
async def web_login(request: Request, config=Depends(get_config), player_service: PlayerService = Depends(get_player_service)):
    login_state = request.cookies.get("login_state")
    if login_state is not None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Already logged in"})

    if request.method == "POST":
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid username or password"})

        player = await player_service.from_username(username)
        if not player:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})
        is_valid_password = await player_service.check_password(player.id, password, None)
        if not is_valid_password:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid username or password"})

        response = templates.TemplateResponse(request, "success.html", {"success_message": success_str("Login successful")})
        response.set_cookie(
            "login_state",
            f"{username}-{player.id}-{utils.make_md5(f'{username}-{player.id}-{config.login_key}')}",
            max_age=60 * 60 * 24 * 30 * 12,
        )

        return response

    return templates.TemplateResponse(request, "web_login.html")
