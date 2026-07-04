from typing import Optional

from fastapi import APIRouter, Query, Request

from objects.beatmap import Beatmap
from objects.score import Score
import utils.pp
import utils
from .models.score import ScoreModel
from .models.responses import ScoreSuccessResponse
from handlers.response import ApiResponse

router = APIRouter()


async def calculate(
    md5: Optional[str],
    bid: Optional[int],
    acc: float,
    miss: int,
    combo: Optional[int],
    mods: str,
):
    score = Score()
    bmap = None

    if md5:
        bmap = await Beatmap.from_md5(md5)
    if bid:
        bmap = await Beatmap.from_bid(bid)

    if bmap is None:
        return ApiResponse.not_found("Beatmap not found")
    score.bmap = bmap
    score.md5 = score.bmap.md5

    if acc is not None:
        score.acc = acc
    if miss is not None:
        score.hmiss = miss
    if combo is not None:
        score.max_combo = combo
    if mods is not None:
        score.mods = mods

    score.pp = await utils.pp.PPCalculator.from_score(score)
    if score.pp is False:
        return ApiResponse.internal_error("Failed to calculate performance points.")
    try:
        await score.pp.calc(api=True)
    except Exception:
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


@router.get("", response_model=ScoreSuccessResponse)
async def calculate_get(
    request: Request,
    md5: Optional[str] = Query(None),
    bid: Optional[int] = Query(None),
    acc: float = Query(100),
    miss: int = Query(0),
    combo: Optional[int] = Query(None),
    mods: str = Query(""),
):
    return await calculate(md5, bid, acc, miss, combo, mods)


@router.post("", response_model=ScoreSuccessResponse)
async def calculate_post(request: Request):
    form = await request.form()
    md5 = form.get("md5")
    bid = int(form["bid"]) if form.get("bid") else None
    acc = float(form.get("acc", 100))
    miss = int(form.get("miss", 0))
    combo = int(form["combo"]) if form.get("combo") else None
    mods = form.get("mods", "")
    return await calculate(md5, bid, acc, miss, combo, mods)
