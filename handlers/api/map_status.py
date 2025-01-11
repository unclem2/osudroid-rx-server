from quart import Blueprint
from objects.beatmap import Beatmap, RankedStatus

bp = Blueprint("map_status", __name__)

forced_route = "/api/v2/md5/<string:md5>"


@bp.route("/")
async def map_status(md5: str):
    map = await Beatmap.from_md5(md5)
    if map is None:
        return {"md5": "", "ranked": -1}
    await map.download()

    if map.status == RankedStatus.Whitelisted:
        map.status = 1

    return map.as_json
