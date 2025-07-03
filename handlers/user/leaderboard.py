from quart import Blueprint, render_template, request
from objects import glob
from utils import get_countries

bp = Blueprint("user_leaderboard", __name__)


@bp.route("/")
async def leaderboard():
    args = request.args
    sortby = args.get("sortby", "pp").lower()
    country = args.get("country", "").upper()

    valid_sortby = {"score", "pp"}
    if sortby not in valid_sortby:
        sortby = "pp"

    if sortby == "score":
        select_fields = "stats.id, stats.plays, users.username, stats.rscore"
        rank_field = "stats.country_score_rank" if country else "stats.score_rank"
        order_field = "stats.rscore"
    else:
        select_fields = "stats.id, stats.pp, stats.plays, users.username"
        rank_field = "stats.country_pp_rank" if country else "stats.pp_rank"
        order_field = "stats.pp"

    query = (
        f"SELECT {select_fields}, {rank_field} "
        "FROM stats "
        "INNER JOIN users ON stats.id = users.id "
    )
    params = []

    if country:
        query += "WHERE users.country = $1 "
        params.append(country)

    query += f"ORDER BY {order_field} DESC"

    players_stats = await glob.db.fetchall(query, params)
    countries = await get_countries()

    return await render_template(
        "leaderboard.jinja",
        leaderboard=players_stats,
        country=country if country else None,
        countries=countries,
        sortby=sortby,
    )
