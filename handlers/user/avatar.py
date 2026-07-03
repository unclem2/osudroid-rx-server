from quart import Blueprint, send_file
import pathlib

bp = Blueprint("user_avatar", __name__)

forced_route = "/user/avatar/<int:uid>.png"


@bp.route("/")
async def avatar(uid: int):
    user_avatar = pathlib.Path(f"/srv/odrx_storage/avatar/{uid}.png")
    if not user_avatar.exists():
        user_avatar = pathlib.Path("/srv/odrx_storage/avatar/default.png")

    return await send_file(user_avatar, mimetype="image/png")
