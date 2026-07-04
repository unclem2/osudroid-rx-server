import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from objects import glob
import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def allowed_file(filename):
    allowed_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@router.post("")
async def set_banner(request: Request):
    auth_cookie = request.cookies.get("login_state")
    if not auth_cookie:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Not logged in"})

    try:
        username, player_id, auth_hash = auth_cookie.split("-")
        if (
            utils.check_md5(
                f"{username}-{player_id}-{glob.config.login_key}", auth_hash
            )
            == False
        ):
            return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})
        player_id = int(player_id)
    except ValueError:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid login state"})

    form = await request.form()

    if "banner" not in form:
        return templates.TemplateResponse(request, "error.html", {"error_message": "No banner file provided"})

    file = form.get("banner")
    if file.filename == "":
        return templates.TemplateResponse(request, "error.html", {"error_message": "No selected file"})

    p = glob.players.get(username=username)
    if not p or p.id != player_id:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    if file and allowed_file(file.filename):
        filename = f"{p.id}.png"
        file_path = os.path.join("data/banner", filename)
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        return templates.TemplateResponse(request, "success.html", {"success_message": "Banner uploaded successfully"})
    else:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid file format"})
