from quart import Blueprint, render_template, request
from objects import glob

bp = Blueprint("user_leaderboard", __name__)

async def get_countries():
    countries = await glob.db.fetchall("SELECT DISTINCT country FROM users WHERE country IS NOT NULL ORDER BY country")
    return [row["country"] for row in countries]


@bp.route("/")
async def leaderboard():
    args = request.args
    type = args.get("sortby", "pp").lower()
    
    if type == "score":
        players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.plays, users.username, stats.rscore, stats.score_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id ORDER BY stats.rscore DESC"
        )
    else:
        players_stats = await glob.db.fetchall(
            "SELECT stats.id, stats.pp_rank, stats.pp, stats.plays, users.username "
            "FROM stats "
            "INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC"
        )

    return await render_template("leaderboard.jinja", leaderboard=players_stats, sortby=type, countries=await get_countries())

