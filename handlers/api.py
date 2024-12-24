from quart import Blueprint, request, jsonify
import aiohttp
from objects import glob
from objects.beatmap import Beatmap, RankedStatus
from objects.score import Score
import utils.pp
from handlers.response import Failed
from dotenv import load_dotenv
import os

load_dotenv()

bp = Blueprint('api', __name__)
bp.prefix = '/api/'


@bp.route('/get_online')
async def get_online():
    online_players = [_ for _ in glob.players if _.online]
    return {'online': len(online_players)}



@bp.route('/get_user')
async def get_user():
    args = request.args

    if 'id' not in args and 'name' not in args:
        return 'Need id or name', 400

    if 'id' in args:
        if not args['id'].isdecimal():
            return 'Invalid id', 400

        player = glob.players.get(id=int(args['id']))
    else:
        if len(args['name']) < 2:
            return 'Invalid name', 400

        player = glob.players.get(name=args['name'])


    if not player:
        return 'Player not found', 404

    return player.as_json


@bp.route('/get_scores')
async def get_scores():
    params = request.args

    limit = min(int(params.get('limit', 50)), 50)
    id = int(params.get('id', 0))

    scores = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 '
        'ORDER BY id DESC LIMIT $2',
        [id, limit]
    )

    if len(scores) == 0:
        return "No scores found.", 400
    if len(scores) > 0:
        return jsonify(scores)


@bp.route('/leaderboard')
async def leaderboard():
    players_stats = await glob.db.fetchall(
        'SELECT stats.id, stats.rank, stats.pp, stats.plays, users.username '
        'FROM stats '
        'INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC'
    )
    return jsonify(players_stats)


@bp.route('/top_scores')
async def top_scores():
    params = request.args
    id = int(params.get('id'))
    top_scores = await glob.db.fetchall(
        'SELECT id, status, maphash, score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 AND "status" = 2 AND maphash IN (SELECT md5 FROM maps WHERE status IN (1, 4, 5))'
        'ORDER BY pp DESC',
        [id]
    )
    return jsonify(top_scores) if top_scores else {'No score found.'}


#bot endpoints

@bp.route('/recent')
async def recent():
    params = request.args
    id = int(params.get('id'))
    index = int(params.get('index'))
    recent = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp FROM scores WHERE "playerid" = $1 '
        'ORDER BY id DESC OFFSET $2',
        [id, index]
    )
    return jsonify(recent) if len(recent) > 0 else 'No score found.'

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
    score.max_combo =  int(data.get('combo', score.bmap.max_combo))
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


# client endpoints
@bp.route('/update.php')
async def send_update():
    data = {
        "version_code": 1727108920,
        "link": "https://github.com/unclem2/osudroid-rx-server/releases/download/v1.13/osu.droid-1.13.240923.-debug-2024-09-23.apk",
        "changelog": "public release"
    }
    return data


@bp.route('/v2/md5/<string:md5>')
async def map_status(md5: str):
    map = await Beatmap.from_md5(md5)
    if map is None:
        return {'md5': '', 'ranked': -1}
    await map.download()

    if map.status == RankedStatus.Whitelisted:
        map.status = 1

    map_data = {

        "md5": md5,
        "ranked": map.status
    }
    return map_data



@bp.route('/wl')
async def whitelist():
    maps = await glob.db.fetchall('SELECT md5 FROM maps WHERE status = 5')
    return jsonify(maps)


@bp.route('/wl_add', methods=['GET'])
async def whitelist_add():
    data = request.args
    if data.get('key') != os.getenv("WL_KEY"):
        return {'status': 'error', 'message': 'Key not specified or incorrect.'}
    if data.get('md5') is not None:
        map = await Beatmap.from_md5(data.get('md5'))
    if data.get('bid') is not None:
        map = await Beatmap.from_bid_osuapi(data.get('bid'))
    if map is None:
        return {'status': 'error', 'message': 'Map not exist'}
    await map.download()
    await map.update_stats()
    map_data = {
        "title": f"{map.artist} - {map.title} ({map.creator}) [{map.version}]",
        "md5": map.md5,
        "stats": f"CS: {map.cs} AR: {map.ar} OD: {map.od} HP: {map.hp} BPM: {map.bpm} Stars: {map.star}",
        "status": map.status
    }

    return map_data


@bp.route('/wl_remove', methods=['GET'])
async def whitelist_remove():
    data = request.args
    if data.get('key') != os.getenv("WL_KEY"):
        return {'status': 'error', 'message': 'Key not specified or incorrect.'}
    if data.get('md5') is not None:
        await glob.db.execute('UPDATE maps SET status = -2 WHERE md5 = $1', [data.get('md5')])
    if data.get('bid') is not None:
        await glob.db.execute('UPDATE maps SET status = -2 WHERE id = $1', [int(data.get('bid'))])
    return {'status': 'success'}
