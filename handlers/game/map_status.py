from fastapi import APIRouter, Depends

from objects.dependencies.services import get_beatmap_service
from objects.enums.ranked_status import RankedStatus
from objects.services.beatmap import BeatmapService

router = APIRouter()

forced_route = "/api/v2/md5"


@router.get("/{md5}")
async def map_status(md5: str, beatmap_service: BeatmapService = Depends(get_beatmap_service)):
    bmap = await beatmap_service.from_md5(md5)
    if bmap is None:
        return {"md5": "", "ranked": -1}
    if bmap.status == RankedStatus.Whitelisted:
        bmap.status = RankedStatus.Ranked
    if bmap.status == RankedStatus.Blacklisted:
        bmap.status = RankedStatus.Graveyard
    return {"md5": md5, "ranked": bmap.status}
