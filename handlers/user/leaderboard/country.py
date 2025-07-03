from quart import Blueprint, render_template, request
from objects import glob

bp = Blueprint("country_user_leaderboard", __name__)

async def get_countries():
    countries = await glob.db.fetchall("SELECT DISTINCT country FROM users WHERE country IS NOT NULL ORDER BY country")
    return [row["country"] for row in countries]


@bp.route("/<string:country>/")
async def leaderboard_country(country):
    args = request.args
    type = args.get("sortby", "pp").lower()
    
    if type == "score":
        players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.plays, users.username, stats.rscore, stats.country_score_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.rscore DESC", [country.upper()]
        )
        
        return await render_template("leaderboard.jinja", leaderboard=players_stats, country=country, countries=await get_countries(), sortby=type)

    players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.pp, stats.plays, users.username, stats.country_pp_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.pp DESC", [country.upper()]
    )

    return await render_template("leaderboard.jinja", leaderboard=players_stats, country=country, countries=await get_countries(), sortby=type)
