from quart import Blueprint
from objects.beatmap import Beatmap, RankedStatus
from quart import jsonify, request

bp = Blueprint("beatmap", __name__)


@bp.route("/")
async def beatmap():
    data = request.args
    md5 = data.get("md5")
    if not md5:
        return {"error": "Missing md5 parameter"}, 400

    beatmap = await Beatmap.from_md5(md5)
    if beatmap is None:
        return {"md5": "", "ranked": -1}
    await beatmap.download()


    return beatmap.as_json
