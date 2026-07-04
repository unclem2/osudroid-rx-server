from typing import Optional

from fastapi import APIRouter, Query

from objects import glob
from .models.player import PlayerModel
from .models.responses import PlayerSuccessResponse
from objects.player import Player
from handlers.response import ApiResponse

router = APIRouter()


@router.get("", response_model=PlayerSuccessResponse)
async def get_user(
    id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
):
    if not id and not username:
        return ApiResponse.bad_request("Either id or username must be provided.")
    if username is not None and len(username) < 2:
        return ApiResponse.bad_request("Invalid username.")

    if id is not None:
        player = glob.players.get(id=id)
    else:
        player: Player = glob.players.get(username=username)

    if not player:
        return ApiResponse.not_found("User not found")

    return ApiResponse.ok(PlayerModel(**player.as_json))
