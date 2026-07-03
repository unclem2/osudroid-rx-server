from quart import Blueprint, send_file
import pathlib

bp = Blueprint("user_banner", __name__)

forced_route = "/user/banner/<int:uid>.png"


@bp.route("/")
async def banner(uid: int):
    user_banner = pathlib.Path(f".//srv/odrx_storage/banner/{uid}.png")
    if not user_banner.exists():
        user_banner = pathlib.Path(".//srv/odrx_storage/banner/default.png")

    return await send_file(user_banner, mimetype="image/png")
