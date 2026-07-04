from typing import Optional

from fastapi import APIRouter, Query

from handlers.api.models.score import ScoreModel
from handlers.api.models.responses import ScoreListSuccessResponse
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from objects.score import Score

router = APIRouter()


@router.get("", response_model=ScoreListSuccessResponse)
async def beatmap_leaderboard(
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
):
    if not md5 and not bid:
        return ApiResponse.bad_request(
            "Either 'md5' or 'bid' must be provided to retrieve a beatmap."
        )

    if md5:
        bmap = await Beatmap.from_md5(md5)
    elif bid:
        bmap = await Beatmap.from_bid(bid)

    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")

    await bmap.recalc_lb_placements()

    beatmap_lb = await glob.db.fetchall(
        """SELECT * FROM scores WHERE md5 = $1 AND global_placement IS NOT NULL
           ORDER BY global_placement ASC""",
        [bmap.md5],
    )
    if not beatmap_lb:
        return ApiResponse.not_found(
            "No leaderboard entries found for this beatmap"
        )

    leaderboard = []
    for score_data in beatmap_lb:
        score = await Score.from_sql(0, score_data)
        if score:
            leaderboard.append(ScoreModel(**score.as_json))
    return ApiResponse.ok(leaderboard)
