from typing import List, Optional

from fastapi import APIRouter, Query

from handlers.api.models.score import ScoreModel
from handlers.api.models.responses import ScoreListSuccessResponse
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from objects.score import Score

router = APIRouter()


@router.get("", response_model=ScoreListSuccessResponse)
async def get_beatmap_scores(
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
    uid: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
):
    if not md5 and not bid:
        return ApiResponse.bad_request("Either 'md5' or 'bid' must be provided.")
    if not uid and not username:
        return ApiResponse.bad_request("Either 'uid' or 'username' must be provided.")

    if md5:
        bmap = await Beatmap.from_md5(md5)
    elif bid:
        bmap = await Beatmap.from_bid(bid)

    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")

    if uid:
        player = glob.players.get(id=uid)
    elif username:
        player = glob.players.get(username=username)

    if player is None:
        return ApiResponse.not_found("Player not found")

    scores = await glob.db.fetchall(
        """SELECT * FROM scores WHERE md5 = $1 AND playerid = $2
           ORDER BY local_placement ASC""",
        [bmap.md5, player.id],
    )
    if not scores:
        return ApiResponse.not_found("No scores found.")
    leaderboard = []
    for score in scores:
        score_obj = await Score.from_sql(0, score)
        if score_obj:
            leaderboard.append(ScoreModel(**score_obj.as_json))

    return ApiResponse.ok(leaderboard)
