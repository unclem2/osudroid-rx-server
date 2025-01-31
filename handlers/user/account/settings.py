from quart import Blueprint, request, render_template
import utils
import os


bp = Blueprint("user_settings", __name__)


@bp.route("/")
async def settings():
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
    return await render_template("account/settings.jinja")
