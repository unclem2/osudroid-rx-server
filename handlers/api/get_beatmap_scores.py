from handlers.api.models.score import ScoreModel
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response, RequestSchemaValidationError
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.beatmap import BeatmapModel
from typing import List, Optional
from quart import Blueprint
from objects.score import Score


bp = Blueprint("get_beatmap_scores", __name__)

class BeatmapScoresRequest(BaseModel):
    md5: Optional[str] = None
    bid: Optional[int] = None
    uid: Optional[int] = None
    username: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_args(cls, values):
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'md5' or 'bid' must be provided."
            )
        if not values.get("uid") and not values.get("username"):
            raise PydanticCustomError(
                "validation_error",
                "Either 'uid' or 'username' must be provided."
            )
        return values

@bp.route("/", methods=["GET"])
@validate_querystring(BeatmapScoresRequest)
@validate_response(ApiResponse[List[ScoreModel]], 200)
@validate_response(ApiResponse[str], 400)
async def get_beatmap_scores(query_args: BeatmapScoresRequest) -> ApiResponse[List[ScoreModel]]:
    """
    Get user scores for a specific beatmap.(slow yet)
    """
    if query_args.md5:
        beatmap = await Beatmap.from_md5(query_args.md5)
    elif query_args.bid:
        beatmap = await Beatmap.from_bid(query_args.bid)

    if beatmap is None:
        return ApiResponse.not_found("Beatmap not found")

    if query_args.uid:
        player = glob.players.get(id=query_args.uid)
    elif query_args.username:
        player = glob.players.get(username=query_args.username)
    
    if player is None:
        return ApiResponse.not_found("Player not found")
    
    scores = await glob.db.fetchall(
        """SELECT * FROM scores WHERE md5 = $1 AND playerid = $2
           ORDER BY local_placement ASC""",
        [beatmap.md5, player.id]
    )
    if not scores:
        return ApiResponse.not_found("No scores found.")
    leaderboard = []
    for score in scores:
        score_obj = await Score.from_sql(0, score)
        if score_obj:
            leaderboard.append(ScoreModel(**score_obj.as_json))

    return ApiResponse.ok(leaderboard)