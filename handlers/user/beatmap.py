from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_beatmap_service
from objects.services.beatmap import BeatmapService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

forced_route = "/beatmap"


@router.get("", name="beatmap")
async def beatmap_page(
    request: Request,
    bid: int | None = Query(None),
    md5: str | None = Query(None),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
):
    if bid:
        beatmap = await beatmap_service.from_id(bid)
    elif md5:
        beatmap = await beatmap_service.from_md5(md5)
    else:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error_message": "Beatmap ID or MD5 required"},
        )

    if not beatmap:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error_message": "Beatmap not found"},
        )

    return templates.TemplateResponse(
        request,
        "beatmap.html",
        {
            "beatmap": beatmap,
        },
    )
