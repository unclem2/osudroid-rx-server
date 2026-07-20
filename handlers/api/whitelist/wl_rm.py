
from fastapi import APIRouter, Depends, Query

import utils
from config import Config
from handlers.response import ApiResponse
from objects.dependencies.config import get_config
from objects.dependencies.services import get_beatmap_service
from objects.enums.ranked_status import RankedStatus
from objects.services.beatmap import BeatmapService

router = APIRouter()


@router.get("")
async def whitelist_remove(
    key: str = Query(...),
    md5: str | None = Query(None),
    bid: int | None = Query(None),
    config: Config = Depends(get_config),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
):
    if not key:
        return ApiResponse.bad_request("Key must be provided.")
    if not md5 and not bid:
        return ApiResponse.bad_request("Either md5 or bid must be provided.")

    if key != config.wl_key:
        return ApiResponse.forbidden("Invalid key.")

    beatmap = None
    if md5 is not None:
        beatmap = await beatmap_service.from_md5(md5)
    elif bid is not None:
        beatmap = await beatmap_service.from_id(bid)
    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found or missing required attributes.")

    await utils.send_webhook(
        title=f"☆ {round(beatmap.star, 2)} {beatmap.artist} - {beatmap.title} ({beatmap.creator}) [{beatmap.version}]",
        title_url=f"https://osu.ppy.sh/beatmapsets/{beatmap.set_id}#osu/{beatmap.id}",
        thumbnail=f"https://b.ppy.sh/thumb/{beatmap.set_id}l.jpg",
        content=f"**Map Stats: **\n**CS:** {beatmap.cs} | **AR:** {beatmap.ar} | **OD:** {beatmap.od} | **HP:** {beatmap.hp}",
        footer="Map removed from whitelist...",
        url=config.wl_hook,
        isEmbed=True,
    )
    status = await beatmap_service.get_bancho_ranked_status(beatmap)
    await beatmap_service.change_ranked_status(beatmap, status)

    return ApiResponse.ok(beatmap)
