import re
from quart import Blueprint, request, render_template
from objects import glob
from handlers.response import Failed, Success
import hashlib
import utils
import geoip2.database
from objects.player import Player
from argon2 import PasswordHasher
import os
import logging

ph = PasswordHasher()
bp = Blueprint("register", __name__)

php_file = True


@bp.route("/", methods=["GET", "POST"])
async def register():
    if request.method == "POST":
        params = await request.form

        for args in ["username", "password", "email"]:
            if not params.get(args, None):
                return Failed("Not enough argument.")

        # check username
        if glob.players.get(username=params["username"]):
            return Failed("Username already exists.")

        if len(params["username"]) < 2:
            return Failed("Username must be longer than 2 characters.")
        
        if re.fullmatch(r'^[A-Za-z0-9](?:[A-Za-z0-9]|[._](?![._]))+$', params["username"]) is None:
            return Failed("Username contains invalid characters.")
        
        if re.fullmatch(r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])", params["email"]) is None:
            return Failed("Email is not valid.")

        try:
            if os.path.exists("GeoLite2-Country.mmdb"):
                with geoip2.database.Reader("GeoLite2-Country.mmdb") as reader:
                    ip = request.remote_addr
                    response = reader.country(ip)
                    country = response.country.iso_code
        except Exception as e:
            logging.error(f"Failed to get country from ip: {e}")
            country = None

        pasw = params["password"] + "taikotaiko"
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
                params["username"],
                utils.make_safe(params["username"]),
                ph.hash(pasw_hashed),
                "okyeah",
                "NotUsed",
                None,
                None,
                params["email"],
                utils.make_md5(params["email"]),
                0,
                country
            ],
        )

        # also create stats table
        await glob.db.execute("INSERT INTO stats (id) VALUES ($1)", [int(player_id)])
        # create player
        p = await Player.from_sql(player_id)
        glob.players.add(p)

        return await render_template(
            "success.jinja", success_message=Success("Account Created.")
        )
    return await render_template("register.jinja")
