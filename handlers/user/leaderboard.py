from quart import Blueprint, render_template_string
from objects import glob
import html_templates

bp = Blueprint('user_leaderboard', __name__)

php_file = True

@bp.route('/')
async def leaderboard():
    players_stats = await glob.db.fetchall(
        'SELECT stats.id, stats.rank, stats.pp, stats.plays, users.username '
        'FROM stats '
        'INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC'
    )

    return await render_template_string(html_templates.leaderboard_temp, leaderboard=players_stats)
