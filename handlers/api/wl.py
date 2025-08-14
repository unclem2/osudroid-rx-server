from quart import Blueprint, jsonify
from objects import glob

bp = Blueprint("wl", __name__)


@bp.route("/")
async def whitelist():
    """
    one day for sure
    """
    maps = await glob.db.fetchall("SELECT * FROM maps WHERE status = 5")
    return jsonify(maps)
