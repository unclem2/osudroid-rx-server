from typing import List

from fastapi import APIRouter, Query

from objects import glob
from objects.player import Player
from objects.score import Score
from handlers.response import ApiResponse
from .models.score import ScoreModel
from .models.responses import ScoreListSuccessResponse

router = APIRouter()


@router.get("", response_model=ScoreListSuccessResponse)
async def get_scores(
    id: int = Query(...),
    limit: int = Query(100),
):
    if limit < 1 or limit > 100:
        return ApiResponse.bad_request("Limit must be between 1 and 100.")

    player: Player = glob.players.get(id=id)
    scores: List[Score] = await player.top_scores(limit=limit)
    return ApiResponse.ok([ScoreModel(**score.as_json) for score in scores])
