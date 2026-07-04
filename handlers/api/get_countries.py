from fastapi import APIRouter
import utils
from handlers.response import ApiResponse
from .models.responses import CountryListResponse

router = APIRouter()


@router.get("", response_model=CountryListResponse)
async def get_countries():
    countries = await utils.get_countries()
    return ApiResponse.ok([country for country in countries])
