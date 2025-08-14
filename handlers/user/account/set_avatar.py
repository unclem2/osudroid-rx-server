from quart import Blueprint, request, render_template
from objects import glob
import os
import utils
from werkzeug.utils import secure_filename

bp = Blueprint("user_set_avatar", __name__)


def allowed_file(filename):
    allowed_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@bp.route("/", methods=["POST"])
async def set_avatar():
    # Check if the authentication cookie is present
    auth_cookie = request.cookies.get("login_state")
    if not auth_cookie:
        return await render_template("error.jinja", error_message="Not logged in")

    # Validate the cookie format and extract username and player ID
    try:
        username, player_id, auth_hash = auth_cookie.split("-")
        if (
            utils.check_md5(f"{username}-{player_id}-{glob.config.login_key}", auth_hash)
            == False
        ):
            return await render_template(
                "error.jinja", error_message="Invalid login state"
            )
        player_id = int(player_id)
    except ValueError:
        return await render_template("error.jinja", error_message="Invalid login state")

    if request.method == "POST":
        files = await request.files

        # Check if the avatar file is part of the request
        if "avatar" not in files:
            return await render_template(
                "error.jinja", error_message="No avatar file provided"
            )

        file = files.get("avatar")
        if file.filename == "":
            return await render_template(
                "error.jinja", error_message="No selected file"
            )

        # Retrieve player object
        p = glob.players.get(username=username)
        if not p or p.id != player_id:
            return await render_template(
                "error.jinja", error_message="Player not found"
            )

        # Validate and save the avatar file
        if file and allowed_file(file.filename):
            file.filename = f"{p.id}.png"
            filename = secure_filename(file.filename)
            file_path = os.path.join("data/avatar", filename)
            await file.save(file_path)

            return await render_template(
                "success.jinja", success_message="Avatar uploaded successfully"
            )
        else:
            return await render_template(
                "error.jinja", error_message="Invalid file format"
            )
