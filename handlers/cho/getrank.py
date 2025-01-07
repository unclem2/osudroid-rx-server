from objects import glob   
from quart import Blueprint, request
import os
from handlers.response import Failed, Success

bp = Blueprint('getrank', __name__)

php_file = True

@bp.route('/', methods=['POST'])
async def leaderboard():
    params = await request.form

    if 'hash' not in params:
        return Failed('No map hash.')

    res = []
    plays = await glob.db.fetchall(
        "SELECT * FROM scores WHERE maphash = $1 AND status = 2 ORDER BY {order_by} DESC".format(
            order_by='pp' if glob.config.pp_leaderboard else 'score'
        ),
        [params['hash']]
    )
    for play in plays:
        player = glob.players.get(id=int(play['playerid']))

        if os.path.isfile(f'data/avatar/{player.id}.png'):
            avatar = f'{glob.config.host}/user/avatar/{player.id}.png'
        else:
            avatar = f'https://s.gravatar.com/avatar/{player.email_hash}'

        res += ['{play_id} {name} {score} {combo} {rank} {mods} {acc} {avatar}'.format(
            play_id=play['id'],
            name=player.name,
            score=int(play['pp']) if glob.config.pp_leaderboard else play['score'],
            combo=play['combo'],
            rank=play['rank'],
            mods=play['mods'],
            acc=int(play['acc'] * 1000),
            avatar=avatar
        )]

    return Success('\n'.join(res))
