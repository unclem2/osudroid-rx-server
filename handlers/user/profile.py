from quart import Blueprint, render_template, request
from objects import glob
from objects.beatmap import Beatmap
from objects.mods import Mods
import time
import os

bp = Blueprint("user_profile", __name__)

php_file = True


@bp.route("/")
async def profile():
    params = request.args
    player_id = None
    if "login_state" not in request.cookies:
        pass
    if "login_state" in request.cookies:
        player_id = int(request.cookies["login_state"].split("-")[1])
    if "id" in params:
        player_id = int(params["id"])

    if player_id is None:
        return await render_template(
            "error.jinja", error_message="No player ID provided"
        )
    p = glob.players.get(id=player_id)
    if not p:
        return await render_template("error.jinja", error_message="Player not found")

    player_stats = p.stats.as_json

    try:
        recent_scores = await glob.db.fetchall(
            'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
            '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 '
            "ORDER BY id DESC LIMIT $2",
            [p.id, 50],
        )
        for score in recent_scores:
            try:
                bmap = await Beatmap.from_md5_sql(score["maphash"])
                score["map"] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            except:
                score["map"] = score["maphash"]
            score["date"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(score["date"] / 1000)
            )
            score["acc"] = f"{score['acc']:.2f}%"
            score["pp"] = f"{score['pp']:.2f}"
            score["mods"] = f"{Mods(score['mods']).convert_std}"

    except BaseException:
        recent_scores = []

    try:
        top_scores = await glob.db.fetchall(
            'SELECT id, status, maphash, score, combo, rank, acc, "hit300", "hitgeki", '
            '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 AND "status" = 2 AND maphash IN (SELECT md5 FROM maps WHERE status IN (1, 4, 5))'
            "ORDER BY pp DESC LIMIT $2",
            [p.id, 50],
        )
        for score in top_scores:
            try:
                bmap = await Beatmap.from_md5_sql(score["maphash"])
                score["map"] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            except:
                score["map"] = score["maphash"]
            score["date"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(score["date"] / 1000)
            )
            score["acc"] = f"{score['acc']:.2f}%"
            score["pp"] = f"{score['pp']:.2f}"
            score["mods"] = f"{Mods(score['mods']).convert_std}"
    except BaseException:
        top_scores = []
    return await render_template(
        "profile.jinja",
        player=p,
        recent_scores=recent_scores,
        top_scores=top_scores,
        player_stats=player_stats,
    )
