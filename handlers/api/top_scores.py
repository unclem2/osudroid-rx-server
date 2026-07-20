from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service, get_score_service
from objects.services.player import PlayerService
from objects.services.score import ScoreService

router = APIRouter()


@router.get("")
async def top_scores(
    id: int = Query(...),
    limit: int = Query(100),
    player_service: PlayerService = Depends(get_player_service),
    score_service: ScoreService = Depends(get_score_service),
):
    if limit < 1 or limit > 100:
        return ApiResponse.bad_request("Limit must be between 1 and 100.")

    player = await player_service.from_uid(id)
    if not player:
        return ApiResponse.not_found("User not found")

    scores = await score_service.player_top_scores(id, limit)
    return ApiResponse.ok(scores)
