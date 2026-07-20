from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from handlers.response import ApiResponse
from objects.dependencies.services import get_beatmap_service
from objects.services.beatmap import BeatmapService

router = APIRouter()


class BeatmapRequest(BaseModel):
    md5: str | None = None
    bid: int | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_args(cls, values):
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'md5' or 'bid' must be provided to retrieve a beatmap.",
            )
        return values


@router.get("")
async def beatmap(
    md5: str | None = Query(None),
    bid: int | None = Query(None),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
):
    if not md5 and not bid:
        return ApiResponse.bad_request(
            "Either 'md5' or 'bid' must be provided to retrieve a beatmap.",
        )
    if md5:
        beatmap = await beatmap_service.from_md5(md5)
    elif bid:
        beatmap = await beatmap_service.from_id(bid)
    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")
    return ApiResponse.ok(beatmap)
