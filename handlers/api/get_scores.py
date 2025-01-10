from quart import Blueprint, request, jsonify
from objects import glob
import utils
from objects.beatmap import Beatmap

bp = Blueprint("get_scores", __name__)


@bp.route("/")
async def get_scores():
    params = request.args

    limit = int(params.get("limit", 50)) if utils.is_convertable(params.get("limit", 50), int) else 50
    if utils.is_convertable(params.get("id", 0), int):
        id = int(params.get("id", 0))
    else:
        return {"error": "Invalid id."}, 400

    scores = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 '
        "ORDER BY id DESC LIMIT $2",
        [id, limit],
    )

    for score in scores:
        try:
            score["beatmap"] = await Beatmap.from_md5(score["maphash"])
            score["beatmap"] = score["beatmap"].as_json
        except:
            score["beatmap"] = ""
        
    return jsonify(scores)