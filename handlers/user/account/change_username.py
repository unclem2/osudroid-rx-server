import re

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from objects import glob
from objects.player import Player
import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("")
async def change_username(request: Request):
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Not logged in"})

    req = await request.form()
    username, player_id, auth_hash = login_state.split("-")
    if (
        utils.check_md5(
            f"{username}-{player_id}-{glob.config.login_key}", auth_hash
        )
        == False
    ):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})
    new_username = req.get("new_username")

    if not new_username:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid new username"})
    if (
        re.fullmatch(
            r"^[A-Za-z0-9](?:[A-Za-z0-9]|[._](?![._]))+$", new_username
        )
        is None
    ):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Username contains invalid characters."})

    try:
        if glob.players.get(username=new_username):
            return templates.TemplateResponse(request, "error.html", {"error_message": "Username already taken"})
    except Exception:
        pass
    player = glob.players.get(id=int(player_id))
    if not player or player.id != int(player_id):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    res = await glob.db.fetch(
        "SELECT status FROM users WHERE id = $1", [player.id]
    )
    if not res:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})
    safe_username = utils.make_safe(new_username)
    await glob.db.execute(
        "UPDATE users SET username = $1, username_safe = $2 WHERE id = $3",
        [new_username, safe_username, player.id],
    )

    player_new = await Player.from_sql(int(player_id))
    glob.players.add(player_new)
    glob.players.remove(player)

    return templates.TemplateResponse(request, "success.html", {"success_message": "Username changed successfully"})
