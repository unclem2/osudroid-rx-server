from fastapi import APIRouter, Depends

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()


@router.get("")
async def get_online(player_service: PlayerService = Depends(get_player_service)):
    count = await player_service.get_online_players_count()
    return ApiResponse.ok(count)
