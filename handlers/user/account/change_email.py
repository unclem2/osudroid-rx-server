from quart import Blueprint, request, render_template
from objects import glob
import utils
import os


bp = Blueprint("user_change_email", __name__)

@bp.route("/", methods=["POST"])
async def change_email():
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return await render_template("error.jinja", error_message="Not logged in")

    if request.method == "POST":
        req = await request.form
        username, player_id, auth_hash = login_state.split("-")
        if (
            utils.check_md5(f"{username}-{player_id}-{os.getenv('KEY')}", auth_hash)
            == False
        ):
            return await render_template(
                "error.jinja", error_message="Invalid login state"
            )
        new_email = req.get("new_email")

        if not new_email:
            return await render_template(
                "error.jinja", error_message="Invalid new email"
            )

        player = glob.players.get(id=int(player_id))
        if not player or player.id != int(player_id):
            return await render_template(
                "error.jinja", error_message="Player not found"
            )

        res = await glob.db.fetch(
            "SELECT email, status FROM users WHERE id = $1", [player.id]
        )
        if not res:
            return await render_template(
                "error.jinja", error_message="Player not found"
            )

        stored_email = res["email"]
        if new_email == stored_email:
            return await render_template(
                "error.jinja", error_message="New email is the same as the old email"
            )
            
        email_hash = utils.make_md5(f"{new_email}")

        await glob.db.execute(
            "UPDATE users SET email = $1, email_hash = $2 WHERE id = $3",
            [new_email, email_hash, player.id],
        )

        return await render_template(
            "success.jinja", success_message="Email changed successfully"
        )