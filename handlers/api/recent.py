from fastapi import APIRouter, Depends, Query

from handlers.response import ApiResponse
from objects.dependencies.services import get_score_service
from objects.services.score import ScoreService

router = APIRouter()


@router.get("")
async def recent(
    id: int = Query(...),
    offset: int = Query(0),
    score_service: ScoreService = Depends(get_score_service),
):
    if offset < 0:
        return ApiResponse.bad_request(
            "Offset must be greater than or equal to 0."
        )

    score = await score_service.recent_score(id, offset)
    if not score:
        return ApiResponse.not_found("No recent score found.")

    return ApiResponse.ok(score)
