from quart import Blueprint
from quart_schema import validate_response, validate_querystring, RequestSchemaValidationError
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from typing import Optional
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from .models.beatmap import BeatmapModel

bp = Blueprint("beatmap", __name__)

class BeatmapRequest(BaseModel):
    md5: Optional[str] = None
    bid: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def validate_args(cls, values):
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'md5' or 'bid' must be provided to retrieve a beatmap."
            )
        return values

@bp.route("/", methods=["GET"])
@validate_querystring(BeatmapRequest)
@validate_response(ApiResponse[str], 400)
@validate_response(ApiResponse[BeatmapModel], 200)
async def beatmap(query_args: BeatmapRequest) -> ApiResponse[BeatmapModel]:
    """
    Get beatmap.
    """
    if query_args.md5:
        beatmap = await Beatmap.from_md5(query_args.md5)
    elif query_args.bid:
        beatmap = await Beatmap.from_bid(query_args.bid)
    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")
    await beatmap.download()
    return ApiResponse.ok(BeatmapModel(**beatmap.as_json))

@bp.errorhandler(RequestSchemaValidationError)
async def handle_error(error: RequestSchemaValidationError):
    error_message = error.validation_error.errors()[0]
    return ApiResponse.custom(
        status=error_message["type"],
        data=error_message["msg"],
        code=400
    )