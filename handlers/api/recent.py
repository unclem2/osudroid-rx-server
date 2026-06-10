from quart import Blueprint, jsonify, request
from objects import glob
from objects.score import Score
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response
from typing import List
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.score import ScoreModel


bp = Blueprint("recent_scores", __name__)


class RecentRequest(BaseModel):
    id: int
    offset: int = 0

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values):
        if values.get("id") is None:
            raise PydanticCustomError(
                "validation_error", "ID must be provided to retrieve recent scores."
            )
        if int(values.get("offset", 0)) < 0:
            raise PydanticCustomError(
                "validation_error", "Offset must be greater than or equal to 0."
            )
        return values


@bp.route("/")
@validate_querystring(RecentRequest)
@validate_response(ApiResponse[ScoreModel], 200)
@validate_response(ApiResponse[str], 400)
async def recent(query_args: RecentRequest) -> ApiResponse[ScoreModel]:
    """
    Get recent score of a specific user.
    """
    id = query_args.id
    offset = query_args.offset

    recent_id = await glob.db.fetch(
        'SELECT id FROM scores WHERE "playerid" = $1 ' "ORDER BY id DESC OFFSET $2",
        [id, offset],
    )
    if not recent_id:
        return ApiResponse.not_found("No recent score found.")
    score = await Score.from_sql(recent_id["id"])
    return ApiResponse.ok(ScoreModel(**score.as_json))
