from quart import Blueprint, request
from objects.beatmap import Beatmap
from objects.score import Score
import utils.pp

bp = Blueprint('calculate', __name__)

@bp.route('/calculate', methods=['GET', 'POST'])
async def calculate():
    data = request.args
    score = Score()
    if data.get('md5') is not None:
        score.bmap = await Beatmap.from_md5(data.get('md5', ''))
        score.bmap.md5 = data.get('md5', '')
    elif data.get('bid') is not None:
        score.bmap = await Beatmap.from_bid_osuapi(data.get('bid', 0))

    score.acc = float(data.get('acc', 100))
    score.max_combo = int(data.get('combo', score.bmap.max_combo))
    score.hmiss = int(data.get('miss', 0))
    score.mods = data.get('mods', '')

    if score.bmap is None:
        return {'error': 'Map not found'}, 400
    await score.bmap.download()
    score.pp = await utils.pp.PPCalculator.from_md5(score.bmap.md5)
    score.pp.acc = score.acc
    score.pp.hmiss = score.hmiss
    score.pp.max_combo = score.max_combo
    score.pp.mods = score.mods
    score.pp = await score.pp.calc()

    result = {
        "pp": score.pp,
        "title": score.bmap.title,
        "artist": score.bmap.artist,
        "creator": score.bmap.creator,
        "version": score.bmap.version,
        "max_combo": score.max_combo,
        "miss": score.hmiss,
        "mods": score.mods,
        "acc": score.acc,
    }

    return result

