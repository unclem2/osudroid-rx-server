from quart import Blueprint, request
from objects import glob
from objects.beatmap import Beatmap
import os
import utils

bp = Blueprint("wl_add", __name__)


@bp.route("/", methods=["GET"])
async def whitelist_add():
    data = request.args
    if data.get("key", None) != os.getenv("WL_KEY"):
        return {"status": "error", "message": "Key not specified or incorrect."}
    if data.get("md5") is not None:
        map = await Beatmap.from_md5(data.get("md5"))
    elif data.get("bid") is not None:
        if not data.get("bid").isdecimal():
            return {"status": "error", "message": "Invalid beatmap id."}
        map = await Beatmap.from_bid_osuapi(data.get("bid"))
    if map is None:
        return {"status": "error", "message": "Map not exist"}
    await map.download()

    # made by operagx
    await utils.send_webhook(
        title=f"☆ {round(map.star, 2)} {map.artist} - {map.title} ({map.creator}) [{map.version}]",
        title_url=f"https://osu.ppy.sh/beatmapsets/{map.set_id}#osu/{map.id}",
        thumbnail=f"https://b.ppy.sh/thumb/{map.set_id}l.jpg",
        content=f"**Map Stats: **\n**CS:** {map.cs} | **AR:** {map.ar} | **OD:** {map.od} | **HP:** {map.hp}",
        footer="Map added to whitelist...",
        url=glob.config.wl_hook,
        isEmbed=True,
    )
    await glob.db.execute("UPDATE maps SET status = 5 WHERE id = $1", [map.id])

    return map.as_json
