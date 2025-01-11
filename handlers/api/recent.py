from quart import Blueprint, jsonify, request
from objects import glob

bp = Blueprint("recent_scores", __name__)


@bp.route("/")
async def recent():
    params = request.args
    if id := params.get("id"):
        if not id.isdecimal():
            return {"error": "Invalid id."}, 400
        id = int(id)
    else:
        return {"error": "Specify id."}, 400

    if offset := params.get("offset", 0):
        if not offset.isdecimal():
            return {"error": "Invalid offset."}, 400 
        offset = int(offset)

    recent = await glob.db.fetch(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp FROM scores WHERE "playerid" = $1 '
        "ORDER BY id DESC OFFSET $2",
        [id, offset],
    )
    return jsonify(recent) if len(recent) > 0 else "No score found."
