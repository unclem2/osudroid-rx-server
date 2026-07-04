from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from argon2 import PasswordHasher

from objects import glob
from handlers.response import success_str
import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")

php_file = True


@router.api_route("", methods=["GET", "POST"])
async def web_login(request: Request):
    login_state = request.cookies.get("login_state")
    if login_state is not None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Already logged in"})

    if request.method == "POST":
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid username or password"})

        hashed_password = utils.make_md5(f"{password}taikotaiko")

        ph = PasswordHasher()
        player = glob.players.get(username=username)
        if not player:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

        res = await glob.db.fetch(
            "SELECT password_hash, status FROM users WHERE id = $1", [player.id]
        )
        if not res:
            return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

        stored_password_hash = res["password_hash"]
        cached_hashes = glob.cache["hashes"]

        if stored_password_hash in cached_hashes:
            if hashed_password != cached_hashes[stored_password_hash]:
                return templates.TemplateResponse(request, "error.html", {"error_message": "Wrong password"})
        else:
            try:
                ph.verify(stored_password_hash, hashed_password)
            except BaseException:
                return templates.TemplateResponse(request, "error.html", {"error_message": "Wrong password"})

        response = templates.TemplateResponse(request, "success.html", {"success_message": success_str("Login successful")})
        response.set_cookie(
            "login_state",
            f"{username}-{player.id}-{utils.make_md5(f'{username}-{player.id}-{glob.config.login_key}')}",
            max_age=60 * 60 * 24 * 30 * 12,
        )

        return response

    return templates.TemplateResponse(request, "web_login.html")
