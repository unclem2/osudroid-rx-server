from fastapi import APIRouter, Query

from objects import glob
from objects.score import Score
from handlers.response import ApiResponse
from .models.score import ScoreModel
from .models.responses import ScoreSuccessResponse

router = APIRouter()


@router.get("", response_model=ScoreSuccessResponse)
async def recent(
    id: int = Query(...),
    offset: int = Query(0),
):
    if offset < 0:
        return ApiResponse.bad_request(
            "Offset must be greater than or equal to 0."
        )

    recent_id = await glob.db.fetch(
        'SELECT id FROM scores WHERE "playerid" = $1 '
        "ORDER BY id DESC OFFSET $2",
        [id, offset],
    )
    if not recent_id:
        return ApiResponse.not_found("No recent score found.")
    score = await Score.from_sql(recent_id["id"])
    return ApiResponse.ok(ScoreModel(**score.as_json))
