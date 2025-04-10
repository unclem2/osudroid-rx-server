from quart import Blueprint, request, render_template
from objects import glob
from handlers.response import Failed, Success
import hashlib
import utils
from objects.player import Player
from argon2 import PasswordHasher

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
        if glob.players.get(name=params["username"]):
            return Failed("Username already exists.")

        if len(params["username"]) < 2:
            return Failed("Username must be longer than 2 characters.")

        pasw = params["password"] + "taikotaiko"
        md5_hash = hashlib.md5()
        md5_hash.update(pasw.encode("utf-8"))
        pasw_hashed = md5_hash.hexdigest()

        player_id = await glob.db.execute(
            """
        INSERT INTO users (
            prefix, username, username_safe, password_hash, device_id, sign, avatar_id, custom_avatar, email, email_hash, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id
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
