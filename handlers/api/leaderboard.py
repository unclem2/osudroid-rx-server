
from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()


@router.get("")
async def leaderboard(
    type: str = Query("pp"),
    country: str | None = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    player_service: PlayerService = Depends(get_player_service),
):
    players = await player_service.get_leaderboard(type, country, limit, offset)
    return ApiResponse.ok(players)
