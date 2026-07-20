
from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import (
    get_beatmap_service,
    get_player_service,
    get_score_service,
)
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService
from objects.services.score import ScoreService

router = APIRouter()


@router.get("")
async def get_beatmap_scores(
    md5: str | None = Query(None),
    bid: int | None = Query(None),
    uid: int | None = Query(None),
    username: str | None = Query(None),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
    player_service: PlayerService = Depends(get_player_service),
    score_service: ScoreService = Depends(get_score_service),
):
    if not md5 and not bid:
        return ApiResponse.bad_request("Either 'md5' or 'bid' must be provided.")
    if not uid and not username:
        return ApiResponse.bad_request("Either 'uid' or 'username' must be provided.")

    if md5:
        bmap = await beatmap_service.from_md5(md5)
    elif bid:
        bmap = await beatmap_service.from_id(bid)

    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")

    if uid:
        player = await player_service.from_uid(uid)
    elif username:
        player = await player_service.from_username(username)

    if player is None:
        return ApiResponse.not_found("Player not found")

    scores = await score_service.player_beatmap_scores(player.id, bmap.md5)
    if not scores:
        return ApiResponse.not_found("No scores found.")

    return ApiResponse.ok(scores)
