from quart import Blueprint, render_template, request
from objects import glob

bp = Blueprint("user_leaderboard", __name__)

php_file = True


@bp.route("/")
async def leaderboard():
    players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.pp_rank, stats.pp, stats.plays, users.username, stats.rscore, stats.score_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC"
    )

    return await render_template("leaderboard.jinja", leaderboard=players_stats)
