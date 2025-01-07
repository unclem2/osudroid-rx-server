from quart import Blueprint

bp = Blueprint('update', __name__)

php_file = True

@bp.route('/')
async def send_update():
    data = {
        "version_code": 1735348672,
        "link": "https://github.com/unclem2/osudroid-rx-server/releases/download/v1.13.1/osu.droid-1.13.241228.-debug-2024-12-28.apk",
        "changelog": "new domain"
    }
    return data

