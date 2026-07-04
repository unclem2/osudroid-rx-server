from typing import Optional

from fastapi import APIRouter, Query

from objects import glob
from objects.beatmap import Beatmap, RankedStatus
from handlers.response import ApiResponse
from .models.beatmap import BeatmapModel
from .models.responses import BeatmapSuccessResponse
import utils

router = APIRouter()


@router.get("", response_model=BeatmapSuccessResponse)
async def whitelist_remove(
    key: str = Query(...),
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
):
    if not key:
        return ApiResponse.bad_request("Key must be provided.")
    if md5 is None and bid is None:
        return ApiResponse.bad_request("Either md5 or bid must be provided.")

    if key != glob.config.wl_key:
        return ApiResponse.forbidden("Invalid key.")

    bmap = (
        await Beatmap.from_md5(md5)
        if md5 is not None
        else await Beatmap.from_bid(bid)
    )
    if bmap is None:
        return ApiResponse.not_found("Beatmap not found or missing required attributes.")

    if md5 is not None:
        await glob.db.execute(
            "UPDATE maps SET status = -3 WHERE md5 = $1", [md5]
        )
    elif bid is not None:
        await glob.db.execute(
            "UPDATE maps SET status = -3 WHERE id = $1", [int(bid)]
        )
    bmap.status = RankedStatus.Blacklisted
    await utils.send_webhook(
        title=f"☆ {round(bmap.star, 2)} {bmap.artist} - {bmap.title} ({bmap.creator}) [{bmap.version}]",
        title_url=f"https://osu.ppy.sh/beatmapsets/{bmap.set_id}#osu/{bmap.id}",
        thumbnail=f"https://b.ppy.sh/thumb/{bmap.set_id}l.jpg",
        content=f"**Map Stats: **\n**CS:** {bmap.cs} | **AR:** {bmap.ar} | **OD:** {bmap.od} | **HP:** {bmap.hp}",
        footer="Map removed from whitelist...",
        url=glob.config.wl_hook,
        isEmbed=True,
    )

    return ApiResponse.ok(data=BeatmapModel(**bmap.as_json))
