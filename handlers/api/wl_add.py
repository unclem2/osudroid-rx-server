from typing import Optional

from fastapi import APIRouter, Query

from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from .models.beatmap import BeatmapModel
from .models.responses import BeatmapSuccessResponse
import utils

router = APIRouter()


@router.get("", response_model=BeatmapSuccessResponse)
async def whitelist_add(
    key: str = Query(...),
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
):
    if not key:
        return ApiResponse.bad_request("Key must be provided.")
    if not md5 and not bid:
        return ApiResponse.bad_request("Either md5 or bid must be provided.")

    if key != glob.config.wl_key:
        return ApiResponse.forbidden("Invalid key.")

    bmap = None
    if md5 is not None:
        bmap = await Beatmap.from_md5(md5)
    elif bid is not None:
        bmap = await Beatmap.from_bid(bid)
    if bmap is None:
        return ApiResponse.not_found("Beatmap not found or missing required attributes.")

    glob.task_manager.add_task(bmap.download())

    await utils.send_webhook(
        title=f"☆ {round(bmap.star, 2)} {bmap.artist} - {bmap.title} ({bmap.creator}) [{bmap.version}]",
        title_url=f"https://osu.ppy.sh/beatmapsets/{bmap.set_id}#osu/{bmap.id}",
        thumbnail=f"https://b.ppy.sh/thumb/{bmap.set_id}l.jpg",
        content=f"**Map Stats: **\n**CS:** {bmap.cs} | **AR:** {bmap.ar} | **OD:** {bmap.od} | **HP:** {bmap.hp}",
        footer="Map added to whitelist...",
        url=glob.config.wl_hook,
        isEmbed=True,
    )
    await glob.db.execute("UPDATE maps SET status = 5 WHERE id = $1", [bmap.id])

    return ApiResponse.ok(BeatmapModel(**bmap.as_json))
