
from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()

ALLOWED_LEADERBOARD_TYPES = {"pp", "score"}


@router.get("")
async def leaderboard(
    type: str = Query("pp"),
    country: str | None = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    player_service: PlayerService = Depends(get_player_service),
):
    if type not in ALLOWED_LEADERBOARD_TYPES:
        type = "pp"
    if limit < 1 or limit > 500:
        return ApiResponse.bad_request("Limit must be between 1 and 500.")
    if offset < 0:
        return ApiResponse.bad_request("Offset must be >= 0.")
    players = await player_service.get_leaderboard(type, country, limit, offset)
    return ApiResponse.ok(players)
