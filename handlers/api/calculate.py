from quart import Blueprint, request
from objects.beatmap import Beatmap
from objects.score import Score
import utils.pp
import utils
from typing import Optional
from quart_schema import (
    RequestSchemaValidationError,
    validate_request,
    validate_response,
    validate_querystring,
)
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.score import ScoreModel
from handlers.response import ApiResponse


bp = Blueprint("calculate", __name__)


class CalculateRequest(BaseModel):
    md5: Optional[str] = None
    bid: Optional[int] = None
    acc: Optional[float] = 100
    miss: Optional[int] = 0
    combo: Optional[int] = None
    mods: Optional[str] = ""

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values):
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'md5' or 'bid' must be provided to retrieve a beatmap.",
            )
        return values


@bp.route("/", methods=["GET"])
@validate_querystring(CalculateRequest)
@validate_response(ApiResponse[ScoreModel], 200)
@validate_response(ApiResponse[str], 404)
@validate_response(ApiResponse[str], 500)
async def calculate_get(query_args: CalculateRequest) -> ApiResponse[ScoreModel]:
    """
    Calculate performance points(GET).
    """
    return await calculate(query_args)


@bp.route("/", methods=["POST"])
@validate_request(CalculateRequest)
@validate_response(ApiResponse[ScoreModel], 200)
@validate_response(ApiResponse[str], 404)
@validate_response(ApiResponse[str], 500)
async def calculate_post(data: CalculateRequest) -> ApiResponse[ScoreModel]:
    """
    Calculate performance points(POST).
    """
    return await calculate(data)


async def calculate(data: CalculateRequest):
    score = Score()

    if data.md5:
        bmap = await Beatmap.from_md5(data.md5)
    if data.bid:
        bmap = await Beatmap.from_bid(data.bid)

    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")
    score.bmap = bmap
    score.md5 = score.bmap.md5

    if data.acc is not None:
        score.acc = data.acc
    if data.miss is not None:
        score.hmiss = data.miss
    if data.combo is not None:
        score.max_combo = data.combo
    if data.mods is not None:
        score.mods = data.mods

    score.pp = await utils.pp.PPCalculator.from_score(score)
    if score.pp is False:
        return ApiResponse.internal_error("Failed to calculate performance points.")
    try:
        await score.pp.calc(api=True)
    except:
        return ApiResponse.internal_error("Failed to calculate performance points.")

    score.bmap.star = score.pp.difficulty
    result = {
        "bmap": score.bmap.as_json,
        "pp": score.pp.calc_pp,
        "acc": score.acc,
        "hmiss": score.hmiss,
        "max_combo": score.pp.max_combo,
        "mods": score.mods,
        "difficulty": score.pp.difficulty,
    }
    return ApiResponse.ok(ScoreModel(**result))


@bp.errorhandler(RequestSchemaValidationError)
async def handle_validation_error(error: RequestSchemaValidationError):
    """
    Handle validation errors for request schema.
    """
    error_message = error.validation_error.errors()[0]
    return ApiResponse.custom(
        status=error_message["type"], data=error_message["msg"], code=400
    )
