from quart import Blueprint, jsonify, request
from objects import glob

bp = Blueprint("leaderboard", __name__)


@bp.route("/")
async def leaderboard():
    args = request.args
    players_stats = (
        await glob.db.fetchall(
            "SELECT stats.id, stats.pp_rank, stats.pp, stats.plays, users.username, users.country "
            "FROM stats "
            "INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC"
        )
        if args.get("type") != "score"
        else await glob.db.fetchall(
            "SELECT stats.id, stats.score_rank, stats.rscore, stats.plays, users.username, users.country "
            "FROM stats "
            "INNER JOIN users ON stats.id = users.id ORDER BY stats.rscore DESC"
        )
    )
    return jsonify(players_stats)


@bp.route("/country/<string:country>/")
async def leaderboard_country(country):
    args = request.args
    players_stats = (
        await glob.db.fetchall(
            "SELECT stats.id, stats.country_pp_rank, stats.pp, stats.plays, users.username, users.country "
            "FROM stats "
            "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.pp DESC",
            [country.upper()],
        )
        if args.get("type") != "score"
        else await glob.db.fetchall(
            "SELECT stats.id, stats.country_score_rank, stats.rscore, stats.plays, users.username, users.country "
            "FROM stats "
            "INNER JOIN users ON stats.id = users.id WHERE country = $1 ORDER BY stats.rscore DESC",
            [country.upper()],
        )
    )
    return jsonify(players_stats)
