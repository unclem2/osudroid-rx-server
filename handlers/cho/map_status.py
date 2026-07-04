from fastapi import APIRouter

from objects.beatmap import Beatmap, RankedStatus
from objects import glob

router = APIRouter()

forced_route = "/api/v2/md5"


@router.get("/{md5}")
async def map_status(md5: str):
    bmap = await Beatmap.from_md5(md5)
    if bmap is None:
        return {"md5": "", "ranked": -1}
    if bmap.status == RankedStatus.Whitelisted:
        bmap.status = RankedStatus.Ranked
    if bmap.status == RankedStatus.Blacklisted:
        bmap.status = RankedStatus.Graveyard
    glob.task_manager.add_task(bmap.download())
    return {"md5": md5, "ranked": bmap.status}
