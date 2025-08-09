from quart import Blueprint, request, render_template
from objects import glob
import os
import utils
from argon2 import PasswordHasher

bp = Blueprint("user_change_password", __name__)


@bp.route("/", methods=["POST"])
async def change_password():
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return await render_template("error.jinja", error_message="Not logged in")

    if request.method == "POST":
        req = await request.form
        username, player_id, auth_hash = login_state.split("-")
        if (
            utils.check_md5(f"{username}-{player_id}-{glob.config.login_key}", auth_hash)
            == False
        ):
            return await render_template(
                "error.jinja", error_message="Invalid login state"
            )
        old_password = req.get("old_password")
        new_password = req.get("new_password")
        new_confirm_password = req.get("confirm_password")
        if new_password != new_confirm_password:
            return await render_template(
                "error.jinja", error_message="Passwords do not match"
            )

        if not old_password or not new_password:
            return await render_template(
                "error.jinja", error_message="Invalid old or new password"
            )

        hashed_old_password = utils.make_md5(f"{old_password}taikotaiko")
        hashed_new_password = utils.make_md5(f"{new_password}taikotaiko")

        ph = PasswordHasher()

        player = glob.players.get(id=int(player_id))
        if not player or player.id != int(player_id):
            return await render_template(
                "error.jinja", error_message="Player not found"
            )

        res = await glob.db.fetch(
            "SELECT password_hash, status FROM users WHERE id = $1", [player.id]
        )
        if not res:
            return await render_template(
                "error.jinja", error_message="Player not found"
            )

        stored_password_hash = res["password_hash"]

        try:
            ph.verify(stored_password_hash, hashed_old_password)
        except BaseException:
            return await render_template("error.jinja", error_message="Wrong password")
        new_password_hash = ph.hash(hashed_new_password)
        await glob.db.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            [new_password_hash, player.id],
        )
        return await render_template(
            "success.jinja", success_message="Password changed successfully"
        )
