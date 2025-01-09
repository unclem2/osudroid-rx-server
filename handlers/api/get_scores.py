from quart import Blueprint, request, jsonify
from objects import glob

bp = Blueprint("get_scores", __name__)


@bp.route("/")
async def get_scores():
    params = request.args

    limit = min(int(params.get("limit", 50)), 50)
    id = int(params.get("id", 0))

    scores = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 '
        "ORDER BY id DESC LIMIT $2",
        [id, limit],
    )

    if len(scores) == 0:
        return "No scores found.", 400
    if len(scores) > 0:
        return jsonify(scores)
