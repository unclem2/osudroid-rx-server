from quart import Blueprint
from objects import glob

bp = Blueprint("update", __name__)

php_file = True


@bp.route("/")
async def send_update():
    data = {
        "version_code": glob.config.client_version_code,
        "link": glob.config.client_link,
        "changelog": glob.config.client_changelog,
    }

    return f"{data}"
