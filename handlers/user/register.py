import re

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

import utils
from config import Config
from handlers.response import Failed, success_str
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

ph = PasswordHasher()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

php_file = True


@router.api_route("", methods=["GET", "POST"])
async def register(request: Request, player_service: PlayerService = Depends(get_player_service), config: Config = Depends(get_config)):
    if request.method == "POST":
        form = await request.form()

        for args in ["username", "password", "email"]:
            if not form.get(args, None):
                return Failed("Not enough argument.")

        if len(form["username"]) < 2:
            return Failed("Username must be longer than 2 characters.")

        if await player_service.from_username(form["username"]):
            return Failed("Username already exists.")

        if (
            re.fullmatch(
                r"^[A-Za-z0-9](?:[A-Za-z0-9]|[._](?![._]))+$", str(form["username"]),
            )
            is None
        ):
            return Failed("Username contains invalid characters.")

        if (
            re.fullmatch(
                r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])",
                str(form["email"]),
            )
            is None
        ):
            return Failed("Email is not valid.")

        player = await player_service.new(form["username"], form["password"], form.get("deviceID", ""), form["email"])

        response = templates.TemplateResponse(request, "success.html", {"success_message": success_str("Account Created.")})
        username = form["username"]
        response.set_cookie(
            "login_state",
            f"{username}-{player.id}-{utils.make_md5(f'{username}-{player.id}-{config.login_key}')}",
            max_age=60 * 60 * 24 * 30 * 12,
        )

        return response

    return templates.TemplateResponse(request, "register.html")
