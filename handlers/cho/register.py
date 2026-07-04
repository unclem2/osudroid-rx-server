import re
import os
import logging
import hashlib

from fastapi import APIRouter, Request
from argon2 import PasswordHasher
import geoip2.database

from objects import glob
from handlers.response import Failed, success_str
import utils
from objects.player import Player
from fastapi.templating import Jinja2Templates

ph = PasswordHasher()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

php_file = True


@router.api_route("", methods=["GET", "POST"])
async def register(request: Request):
    if request.method == "POST":
        form = await request.form()

        for args in ["username", "password", "email"]:
            if not form.get(args, None):
                return Failed("Not enough argument.")

        if glob.players.get(username=form["username"]):
            return Failed("Username already exists.")

        if len(form["username"]) < 2:
            return Failed("Username must be longer than 2 characters.")

        if (
            re.fullmatch(
                r"^[A-Za-z0-9](?:[A-Za-z0-9]|[._](?![._]))+$", form["username"]
            )
            is None
        ):
            return Failed("Username contains invalid characters.")

        if (
            re.fullmatch(
                r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])",
                form["email"],
            )
            is None
        ):
            return Failed("Email is not valid.")

        try:
            country = None
            if os.path.exists("GeoLite2-Country.mmdb"):
                with geoip2.database.Reader("GeoLite2-Country.mmdb") as reader:
                    ip = request.client.host
                    response = reader.country(ip)
                    country = response.country.iso_code
        except Exception as e:
            logging.error(f"Failed to get country from ip: {e}")
            country = None

        pasw = form["password"] + "taikotaiko"
        md5_hash = hashlib.md5()
        md5_hash.update(pasw.encode("utf-8"))
        pasw_hashed = md5_hash.hexdigest()

        player_id = await glob.db.execute(
            """
        INSERT INTO users (
            prefix, username, username_safe, password_hash, device_id, sign, avatar_id, custom_avatar, email, email_hash, status, country
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) RETURNING id
        """,
            [
                None,
                form["username"],
                utils.make_safe(form["username"]),
                ph.hash(pasw_hashed),
                "okyeah",
                "NotUsed",
                None,
                None,
                form["email"],
                utils.make_md5(form["email"]),
                0,
                country,
            ],
        )

        await glob.db.execute("INSERT INTO stats (id) VALUES ($1)", [int(player_id)])
        p = await Player.from_sql(player_id)
        glob.players.add(p)

        response = templates.TemplateResponse(request, "success.html", {"success_message": success_str("Account Created.")})
        username = form["username"]
        response.set_cookie(
            "login_state",
            f"{username}-{player_id}-{utils.make_md5(f'{username}-{player_id}-{glob.config.login_key}')}",
            max_age=60 * 60 * 24 * 30 * 12,
        )

        return response

    return templates.TemplateResponse(request, "register.html")
