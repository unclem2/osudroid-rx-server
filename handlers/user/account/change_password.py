from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from argon2 import PasswordHasher

from objects import glob
import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("")
async def change_password(request: Request):
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
    old_password = req.get("old_password")
    new_password = req.get("new_password")
    new_confirm_password = req.get("confirm_password")
    if new_password != new_confirm_password:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Passwords do not match"})

    if not old_password or not new_password:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid old or new password"})

    hashed_old_password = utils.make_md5(f"{old_password}taikotaiko")
    hashed_new_password = utils.make_md5(f"{new_password}taikotaiko")

    ph = PasswordHasher()

    player = glob.players.get(id=int(player_id))
    if not player or player.id != int(player_id):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    res = await glob.db.fetch(
        "SELECT password_hash, status FROM users WHERE id = $1", [player.id]
    )
    if not res:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    stored_password_hash = res["password_hash"]

    try:
        ph.verify(stored_password_hash, hashed_old_password)
    except BaseException:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Wrong password"})
    new_password_hash = ph.hash(hashed_new_password)
    await glob.db.execute(
        "UPDATE users SET password_hash = $1 WHERE id = $2",
        [new_password_hash, player.id],
    )
    return templates.TemplateResponse(request, "success.html", {"success_message": "Password changed successfully"})
