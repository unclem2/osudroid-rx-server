import re

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("", name="user_change_email")
async def change_email(request: Request, config=Depends(get_config), player_service: PlayerService = Depends(get_player_service)):
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
    new_email = req.get("new_email")

    if not new_email:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid new email"})
    if (
        re.fullmatch(
            r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])",
            new_email,
        )
        is None
    ):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Email is not valid."})

    player = await player_service.from_username(username)
    if not player or player.id != int(player_id):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    await player_service.change_email(player.id, new_email)

    return templates.TemplateResponse(request, "success.html", {"success_message": "Email changed successfully"})
