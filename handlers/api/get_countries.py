from fastapi import APIRouter, Depends

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()


@router.get("")
async def get_countries(player_service: PlayerService = Depends(get_player_service)):
    countries = await player_service.get_countries_list()
    return ApiResponse.ok(countries)
