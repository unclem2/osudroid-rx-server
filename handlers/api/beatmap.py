from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from .models.beatmap import BeatmapModel
from .models.responses import BeatmapSuccessResponse

router = APIRouter()


class BeatmapRequest(BaseModel):
    md5: Optional[str] = None
    bid: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def validate_args(cls, values):
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'md5' or 'bid' must be provided to retrieve a beatmap.",
            )
        return values


@router.get("", response_model=BeatmapSuccessResponse)
async def beatmap(
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
):
    if not md5 and not bid:
        return ApiResponse.bad_request(
            "Either 'md5' or 'bid' must be provided to retrieve a beatmap."
        )
    if md5:
        bmap = await Beatmap.from_md5(md5)
    elif bid:
        bmap = await Beatmap.from_bid(bid)
    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")
    await bmap.download()
    return ApiResponse.ok(BeatmapModel(**bmap.as_json))
