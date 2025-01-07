from quart import Blueprint, jsonify
from objects import glob

bp = Blueprint('leaderboard', __name__)

@bp.route('/')
async def leaderboard():
    players_stats = await glob.db.fetchall(
        'SELECT stats.id, stats.rank, stats.pp, stats.plays, users.username '
        'FROM stats '
        'INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC'
    )
    return jsonify(players_stats)