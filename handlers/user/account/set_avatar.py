import os
import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def allowed_file(filename):
    allowed_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@router.post("", name="user_set_avatar")
async def set_avatar(request: Request, config=Depends(get_config), player_service: PlayerService = Depends(get_player_service)):
    auth_cookie = request.cookies.get("login_state")
    if not auth_cookie:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Not logged in"})

    try:
        username, player_id, auth_hash = auth_cookie.split("-")
        if (
            not utils.check_md5(
                f"{username}-{player_id}-{config.login_key}", auth_hash,
            )
        ):
            return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})
        player_id = int(player_id)
    except ValueError:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})

    form = await request.form()

    if "avatar" not in form:
        return templates.TemplateResponse(request, "error.html", {"error_message": "No avatar file provided"})

    file = form.get("avatar")
    if file.filename == "":
        return templates.TemplateResponse(request, "error.html", {"error_message": "No selected file"})

    player = await player_service.from_username(username)
    if not player or player.id != player_id:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    if file and allowed_file(file.filename):
<<<<<<< HEAD
        filename = f"{player.id}.png"
        file_path = os.path.join("data/avatar", filename)
=======
        filename = f"{p.id}.png"
        file_path = os.path.join("/srv/odrx_storage/dev/avatar", filename)
>>>>>>> 0384a5e50aa8acb4edffaf39ae3958fd60bcf085
        contents = await file.read()
        pathlib.Path(file_path).write_bytes(contents)

        return templates.TemplateResponse(request, "success.html", {"success_message": "Avatar uploaded successfully"})
    return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid file format"})
