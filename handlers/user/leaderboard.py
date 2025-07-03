from quart import Blueprint, render_template, request
from objects import glob
import utils

bp = Blueprint("user_leaderboard", __name__)

php_file = True

@bp.route("/")
async def leaderboard():
    args = request.args
    type = args.get("type")
    
    if type == "score":
        players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.plays, users.username, stats.rscore, stats.score_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id ORDER BY stats.rscore DESC"
        )
        return await render_template("leaderboard_score.jinja", leaderboard=players_stats, countries=await utils.get_countries())
      
    players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.pp_rank, stats.pp, stats.plays, users.username "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC"
    )

    return await render_template("leaderboard.jinja", leaderboard=players_stats, countries=await utils.get_countries())

@bp.route("/country/<string:country>/")
async def leaderboard_country(country):
    args = request.args
    type = args.get("type")
    
    if type == "score":
        players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.plays, users.username, stats.rscore, stats.country_score_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.rscore DESC", [country.upper()]
        )
        
        return await render_template("leaderboard_country_score.jinja", leaderboard=players_stats, country=country, countries=await utils.get_countries())
    
    players_stats = await glob.db.fetchall(
        "SELECT stats.id, stats.pp, stats.plays, users.username, stats.country_pp_rank "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.pp DESC", [country.upper()]
    )

    return await render_template("leaderboard_country.jinja", leaderboard=players_stats, country=country, countries=await utils.get_countries())