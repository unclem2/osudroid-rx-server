from quart import Blueprint, request
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.beatmap import BeatmapModel
from typing import Optional
import utils

bp = Blueprint("wl_remove", __name__)

class WhitelistRemoveRequest(BaseModel):
    key: str
    md5: Optional[str] = None
    bid: Optional[int] = None

    @model_validator(mode="before")
    def validate(cls, values):
        if values.get("key") is None:
            raise PydanticCustomError(
                "validation_error",
                "Key must be provided."
            )
        if values.get("md5") is None and values.get("bid") is None:
            raise PydanticCustomError(
                "validation_error",
                "Either md5 or bid must be provided."
            )
        return values


@bp.route("/", methods=["GET"])
@validate_querystring(WhitelistRemoveRequest)
@validate_response(ApiResponse[str], 200)
@validate_response(ApiResponse[str], 400)
@validate_response(ApiResponse[str], 403)
async def whitelist_remove(query_args: WhitelistRemoveRequest) -> ApiResponse[str]:
    """ 
    Remove a beatmap from the whitelist.
    """
    if query_args.key != glob.config.wl_key:
        return ApiResponse.forbidden("Invalid key.")
    if query_args.md5 is not None:
        await glob.db.execute(
            "UPDATE maps SET status = -2 WHERE md5 = $1", [query_args.md5]
        )
    elif query_args.bid is not None:
        await glob.db.execute(
            "UPDATE maps SET status = -2 WHERE id = $1", [int(query_args.bid)]
        )
    return ApiResponse.ok("Successfully removed map from whitelist.")
