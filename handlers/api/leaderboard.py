from quart import Blueprint, jsonify, request
from objects import glob
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response
from typing import List, Optional
from pydantic import BaseModel, model_validator
from .models.player import PlayerModel
import json

bp = Blueprint("leaderboard", __name__)


class RequestModel(BaseModel):
    type: str = "pp"
    country: Optional[str] = None


@bp.route("/")
@validate_querystring(RequestModel)
@validate_response(ApiResponse[List[PlayerModel]], 200)
async def leaderboard(query_args: RequestModel) -> ApiResponse[List[PlayerModel]]:
    """
    Get user leaderboard(score, pp, country)
    """
    query = """
            SELECT
            users.id, 
            users.username, 
            users.country,
            json_build_object(
                'id', stats.id,
                'pp_rank', stats.pp_rank,
                'pp', stats.pp,
                'acc', stats.acc,
                'tscore', stats.tscore,
                'rscore', stats.rscore,
                'plays', stats.plays,
                'score_rank', stats.score_rank,
                'country_pp_rank', stats.country_pp_rank,
                'country_score_rank', stats.country_score_rank
              ) AS stats
            FROM users
            INNER JOIN stats ON users.id = stats.id
"""

    if query_args.country:
        query += " WHERE users.country = $1"
    if query_args.type == "score":
        query += " ORDER BY stats.rscore DESC"
    else:
        query += " ORDER BY stats.pp DESC"
    if query_args.country:
        players_stats = await glob.db.fetchall(query, [query_args.country.upper()])
    else:
        players_stats = await glob.db.fetchall(query)
    for player in players_stats:
        player["stats"] = json.loads(player["stats"])
    return ApiResponse.ok(PlayerModel(**player) for player in players_stats)


# @bp.route("/country/<string:country>/")
# async def leaderboard_country(country):
#     args = request.args
#     players_stats = (
#         await glob.db.fetchall(
#             "SELECT stats.id, stats.country_pp_rank, stats.pp, stats.plays, users.username, users.country "
#             "FROM stats "
#             "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.pp DESC",
#             [country.upper()],
#         )
#         if args.get("type") != "score"
#         else await glob.db.fetchall(
#             "SELECT stats.id, stats.country_score_rank, stats.rscore, stats.plays, users.username, users.country "
#             "FROM stats "
#             "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.rscore DESC",
#             [country.upper()],
#         )
#     )
#     return jsonify(players_stats)
