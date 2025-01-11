from quart import Blueprint, request, jsonify
from objects import glob

bp = Blueprint("top_scores", __name__)


@bp.route("/")
async def top_scores():
    params = request.args
    id = int(params.get("id"))
    top_scores = await glob.db.fetchall(
        'SELECT id, status, maphash, score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 AND "status" = 2 AND maphash IN (SELECT md5 FROM maps WHERE status IN (1, 4, 5))'
        "ORDER BY pp DESC LIMIT 100",
        [id],
    )
    return jsonify(top_scores) if top_scores else {"No score found."}
