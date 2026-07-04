import json
from typing import Optional

from fastapi import APIRouter, Query

from objects import glob
from handlers.response import ApiResponse
from .models.player import PlayerModel
from .models.responses import PlayerListSuccessResponse

router = APIRouter()


@router.get("", response_model=PlayerListSuccessResponse)
async def leaderboard(
    type: str = Query("pp"),
    country: Optional[str] = Query(None),
):
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

    if country:
        query += " WHERE users.country = $1"
    if type == "score":
        query += " ORDER BY stats.rscore DESC"
    else:
        query += " ORDER BY stats.pp DESC"
    if country:
        players_stats = await glob.db.fetchall(query, [country.upper()])
    else:
        players_stats = await glob.db.fetchall(query)
    for player in players_stats:
        player["stats"] = json.loads(player["stats"])
    return ApiResponse.ok([PlayerModel(**player) for player in players_stats])
