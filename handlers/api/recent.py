from quart import Blueprint, jsonify, request
from objects import glob

bp = Blueprint("recent", __name__)


@bp.route("/recent")
async def recent():
    params = request.args
    id = int(params.get("id"))
    index = int(params.get("index"))
    recent = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp FROM scores WHERE "playerid" = $1 '
        "ORDER BY id DESC OFFSET $2",
        [id, index],
    )
    return jsonify(recent) if len(recent) > 0 else "No score found."
