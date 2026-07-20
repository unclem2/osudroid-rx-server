
from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_beatmap_service, get_score_service
from objects.services.beatmap import BeatmapService
from objects.services.score import ScoreService

router = APIRouter()


@router.get("")
async def beatmap_leaderboard(
    md5: str | None = Query(None),
    bid: int | None = Query(None),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
    score_service: ScoreService = Depends(get_score_service),
):
    if not md5 and not bid:
        return ApiResponse.bad_request(
            "Either 'md5' or 'bid' must be provided to retrieve a beatmap.",
        )

    if md5:
        beatmap = await beatmap_service.from_md5(md5)
    elif bid:
        beatmap = await beatmap_service.from_id(bid)

    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")

    leaderboard = await score_service.beatmap_scores(beatmap.md5)
    return ApiResponse.ok(leaderboard)
