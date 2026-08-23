from fastapi import APIRouter, Depends
from pydantic import BaseModel

from handlers.response import ApiResponse
from objects.dependencies.services import get_recalc_service
from objects.services.recalc import RecalcService

router = APIRouter()


class RecalcScoreRequest(BaseModel):
    score_id: int


@router.post("")
async def recalc_score(
    request: RecalcScoreRequest,
    recalc_service: RecalcService = Depends(get_recalc_service),
):
    score = await recalc_service.recalc_score(request.score_id)
    if not score:
        return ApiResponse.not_found("Score not found")
    return ApiResponse.ok(score)
