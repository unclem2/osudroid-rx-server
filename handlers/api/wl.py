from quart import Blueprint, jsonify
from objects import glob

bp = Blueprint("wl", __name__)


@bp.route("/")
async def whitelist():
    maps = await glob.db.fetchall("SELECT md5 FROM maps WHERE status = 5")
    return jsonify(maps)
