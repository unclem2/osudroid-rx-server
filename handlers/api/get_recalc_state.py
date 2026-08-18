from fastapi import APIRouter

from handlers.response import ApiResponse
from objects.services.recalc import RecalcService

router = APIRouter()


@router.get("")
async def get_recalc_state():
    state = await RecalcService.get_recalc_state()
    return ApiResponse.ok(state)
