import re

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("", name="user_change_username")
async def change_username(request: Request, config=Depends(get_config), player_service: PlayerService = Depends(get_player_service)):
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Not logged in"})

    req = await request.form()
    username, player_id, auth_hash = login_state.split("-")
    if (
        not utils.check_md5(
            f"{username}-{player_id}-{config.login_key}", auth_hash,
        )
    ):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})

    new_username = req.get("new_username")

    if not new_username:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid new username"})
    if (
        re.fullmatch(
            r"^[A-Za-z0-9](?:[A-Za-z0-9]|[._](?![._]))+$", new_username,
        )
        is None
    ):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Username contains invalid characters."})

    if await player_service.from_username(new_username):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Username already taken"})

    player = await player_service.from_username(username)
    if not player or player.id != int(player_id):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    await player_service.change_username(player.id, new_username)

    return templates.TemplateResponse(request, "success.html", {"success_message": "Username changed successfully"})
