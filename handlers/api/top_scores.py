from quart import Blueprint
from objects import glob
from objects.player import Player
from objects.score import Score
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response, RequestSchemaValidationError
from typing import List
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.score import ScoreModel

bp = Blueprint("top_scores", __name__)


class TopScoresRequest(BaseModel):
    id: int
    limit: int = 100

    @model_validator(mode="before")
    def validate(cls, values):
        if values.get("id") is None:
            raise PydanticCustomError(
                "validation_error",
                "UID must be provided to retrieve scores."
            )
        if int(values.get("limit", 0)) < 1 and int(values.get("limit", 0)) > 100:
            raise PydanticCustomError(
                "validation_error",
                "Limit must be lower than 100."
            )

        return values

@bp.route("/", methods=["GET"])
@validate_querystring(TopScoresRequest)
@validate_response(ApiResponse[List[ScoreModel]], 200)
@validate_response(ApiResponse[str], 400)
async def get_scores(query_args: TopScoresRequest) -> ApiResponse[List[ScoreModel]]:
    """
    Get top scores for a specific user.
    """
    player: Player = glob.players.get(id=query_args.id)
    scores: List[Score] = await player.top_scores(limit=query_args.limit)
    return ApiResponse.ok([ScoreModel(**score.as_json) for score in scores])

@bp.errorhandler(RequestSchemaValidationError)
async def handle_validation_error(error: RequestSchemaValidationError):
    """
    Handle validation errors for request schema.
    """
    error_message = error.validation_error.errors()[0]
    return ApiResponse.custom(
        status=error_message["type"],
        data=error_message["msg"],
        code=400
    )