from handlers.api.models.score import ScoreModel
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from quart_schema import (
    validate_querystring,
    validate_response,
    RequestSchemaValidationError,
)
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from typing import List, Optional
from quart import Blueprint
from objects.score import Score

bp = Blueprint("beatmap_leaderboard", __name__)


class BeatmapLeaderboardRequest(BaseModel):
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


@bp.route("/", methods=["GET"])
@validate_querystring(BeatmapLeaderboardRequest)
@validate_response(ApiResponse[List[ScoreModel]], 200)
@validate_response(ApiResponse[str], 400)
async def beatmap_leaderboard(
    query_args: BeatmapLeaderboardRequest,
) -> ApiResponse[List[ScoreModel]]:
    """
    Get beatmap leaderboard.(slow yet)
    """
    if query_args.md5:
        beatmap = await Beatmap.from_md5(query_args.md5)
    elif query_args.bid:
        beatmap = await Beatmap.from_bid(query_args.bid)

    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")

    await beatmap.recalc_lb_placements()

    beatmap_lb = await glob.db.fetchall(
        """SELECT * FROM scores WHERE md5 = $1 AND global_placement IS NOT NULL
           ORDER BY global_placement ASC""",
        [beatmap.md5],
    )
    if not beatmap_lb:
        return ApiResponse.not_found("No leaderboard entries found for this beatmap")

    leaderboard = []
    for score_data in beatmap_lb:
        score = await Score.from_sql(0, score_data)
        if score:
            leaderboard.append(ScoreModel(**score.as_json))
    return ApiResponse.ok(leaderboard)


@bp.errorhandler(RequestSchemaValidationError)
async def handle_error(error: RequestSchemaValidationError):
    error_message = error.validation_error.errors()[0]
    return ApiResponse.custom(
        status=error_message["type"], data=error_message["msg"], code=400
    )
