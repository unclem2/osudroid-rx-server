from typing import List

from fastapi import APIRouter, Query

from objects import glob
from objects.player import Player
from handlers.response import ApiResponse
from .models.score import ScoreModel
from .models.responses import ScoreListSuccessResponse
from objects.score import Score

router = APIRouter()


@router.get("", response_model=ScoreListSuccessResponse)
async def get_scores(
    id: int = Query(...),
    limit: int = Query(50),
):
    if limit < -1:
        return ApiResponse.bad_request("Limit must be greater than -1.")

    player: Player = glob.players.get(id=id)
    scores: List[Score] = await player.get_scores(limit=limit)
    return ApiResponse.ok([ScoreModel(**score.as_json) for score in scores])
