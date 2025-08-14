from quart import Blueprint
from objects.beatmap import Beatmap, RankedStatus
from quart import jsonify
from objects import glob

bp = Blueprint("map_status", __name__)

forced_route = "/api/v2/md5/<string:md5>"


@bp.route("/")
async def map_status(md5: str):
    map = await Beatmap.from_md5(md5)
    if map is None:
        return {"md5": "", "ranked": -1}
    if map.status == RankedStatus.Whitelisted:
        map.status = RankedStatus.Ranked

    glob.task_manager.add_task(map.download())
    return {"md5": md5, "ranked": map.status}
