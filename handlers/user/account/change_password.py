from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("", name="user_change_password")
async def change_password(request: Request, config=Depends(get_config), player_service: PlayerService = Depends(get_player_service)):
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
    old_password = req.get("old_password")
    new_password = req.get("new_password")
    new_confirm_password = req.get("confirm_password")
    if new_password != new_confirm_password:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Passwords do not match"})

    if not old_password or not new_password:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid old or new password"})

    player = await player_service.from_username(username)

    if not player or player.id != int(player_id):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    if await player_service.check_password(player.id, old_password, None) is False:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Wrong password"})

    await player_service.set_password(player.id, new_password)
    return templates.TemplateResponse(request, "success.html", {"success_message": "Password changed successfully"})
