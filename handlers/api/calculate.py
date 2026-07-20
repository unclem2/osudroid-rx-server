
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from handlers.response import ApiResponse
from objects.dependencies.services import get_beatmap_service, get_score_service
from objects.services.beatmap import BeatmapService
from objects.services.score import ScoreService

router = APIRouter(prefix="/score")


class CalculateRequestModel(BaseModel):
    beatmap_id: int | None = None
    md5: str | None = None
    acc: float | None = 100
    miss: int | None = 0
    combo: int | None = None
    h300: int | None = None
    h100: int | None = None
    h50: int | None = None
    hgeki: int | None = None
    hkatsu: int | None = None
    slidertickhits: int | None = None
    sliderendhits: int | None = None
    sliderheadhits: int | None = None
    sliderrepeathits: int | None = None
    mods: list[dict] = []


@router.post("/", response_model=None)
async def calculate(
    request: CalculateRequestModel,
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
    score_service: ScoreService = Depends(get_score_service),
):
    if request.md5:
        beatmap = await beatmap_service.from_md5(request.md5)
    elif request.beatmap_id:
        beatmap = await beatmap_service.from_id(request.beatmap_id)
    else:
        return ApiResponse.bad_request("Either md5 or beatmap_id must be provided.")

    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")

    result = await score_service.calculate(
        beatmap,
        request.mods,
        request.acc,
        request.miss,
        request.combo,
        request.h300,
        request.h100,
        request.h50,
        request.hgeki,
        request.hkatsu,
        request.slidertickhits,
        request.sliderendhits,
        request.sliderheadhits,
        request.sliderrepeathits,
    )

    return ApiResponse.ok(result)
