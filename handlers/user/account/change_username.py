from quart import Blueprint, request, render_template
from objects import glob
import os
import utils


bp = Blueprint("user_change_username", __name__)


@bp.route("/", methods=["POST"])
async def change_username():
    login_state = request.cookies.get("login_state")
    if login_state is None:
        return render_template("error.jinja", error_message="Not logged in")

    if request.method == "POST":
        req = request.form
        username, player_id, auth_hash = login_state.split("-")
        if (
            utils.check_md5(f"{username}-{player_id}-{os.getenv('KEY')}", auth_hash)
            == False
        ):
            return render_template("error.jinja", error_message="Invalid login state")
        new_username = req.get("new_username")
        if not new_username:
            return render_template("error.jinja", error_message="Invalid new username")

        player = glob.players.get(id=int(player_id))
        if not player or player.id != int(player_id):
            return render_template("error.jinja", error_message="Player not found")

        res = await glob.db.fetch("SELECT status FROM users WHERE id = $1", [player.id])
        if not res:
            return render_template("error.jinja", error_message="Player not found")
        safe_username = utils.make_safe(new_username)
        await glob.db.execute(
            "UPDATE users SET username = $1, username_safe = $2 WHERE id = $3",
            [new_username, safe_username, player.id],
        )
        return render_template(
            "success.jinja", success_message="Username changed successfully"
        )
