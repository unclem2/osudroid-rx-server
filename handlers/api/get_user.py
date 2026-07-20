
from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()


@router.get("")
async def get_user(
    id: int | None = Query(None),
    username: str | None = Query(None),
    player_service: PlayerService = Depends(get_player_service),
):
    if not id and not username:
        return ApiResponse.bad_request("Either id or username must be provided.")
    if username is not None and len(username) < 2:
        return ApiResponse.bad_request("Invalid username.")

    if id is not None:
        player = await player_service.from_uid(id)
    else:
        player = await player_service.from_username(username)

    if not player:
        return ApiResponse.not_found("User not found")

    return ApiResponse.ok(player)
