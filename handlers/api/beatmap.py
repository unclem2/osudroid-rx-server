from quart import Blueprint
from objects.beatmap import Beatmap, RankedStatus
from quart import jsonify, request

bp = Blueprint("beatmap", __name__)


@bp.route("/")
async def beatmap():
    data = request.args
    md5 = data.get("md5")
    try:
        map = await Beatmap.from_md5(md5)
        if map is None:
            return {"md5": "", "ranked": -1}
        await map.download()
    except:
        return {"md5": "", "ranked": -1}

    return map.as_json