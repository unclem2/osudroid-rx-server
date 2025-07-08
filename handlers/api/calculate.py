from quart import Blueprint, request, jsonify
from objects.beatmap import Beatmap
from objects.score import Score
import utils.pp
import utils

bp = Blueprint("calculate", __name__)


@bp.route("/", methods=["GET", "POST"])
async def calculate():
    data = request.args
    score = Score()

    if md5 := data.get("md5"):
        try:
            score.bmap = await Beatmap.from_md5(md5)
            score.bmap.md5 = md5
        except AttributeError:
            return {"error": "Specify beatmap id or md5 hash"}, 400
    elif bid := data.get("bid"):
        if bid.isdecimal():
            score.bmap = await Beatmap.from_bid_osuapi(int(bid))
        else:
            return {"error": "Invalid beatmap id. It must be an integer."}, 400
    else:
        return {"error": "Specify beatmap id or md5 hash"}, 400

    if score.bmap is None:
        return {"error": "Beatmap not found"}, 404
    acc = 100
    if acc := data.get("acc"):
        if acc.isdecimal():
            score.acc = float(acc)
          
    miss = 0
    if miss := data.get("miss"):
        if miss.isdecimal():
            score.hmiss = int(miss)

    score.max_combo = score.bmap.max_combo
    if combo := data.get("combo"):
        if combo.isdecimal():
            score.max_combo = int(combo)

    score.pp  = await utils.pp.PPCalculator.from_score(score)
    if score.pp is False:
        return {"error": "Failed to calculate performance points."}, 500
    await score.pp.calc(api=True)

    # Prepare result dictionary
    result = {
        "beatmap": score.bmap.as_json,
        "pp": score.pp.calc_pp,
        "acc": score.acc,
        "hmiss": score.hmiss,
        "max_combo": score.pp.max_combo,
        "mods": score.mods,
    }
    result = jsonify(result)
    return result
