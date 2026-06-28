from quart import Blueprint, render_template, request
from objects import glob
from objects.beatmap import Beatmap
from objects.player import Player
from osudroid_api_wrapper import ModList
import time
import json
import os

bp = Blueprint("user_profile", __name__)

php_file = True


@bp.route("/")
async def profile():
    params = request.args
    player_id = None
    try:
        if "id" in params:
            player_id = int(params["id"])
        elif "uid" in params:
            player_id = int(params["uid"])
        elif "login_state" in request.cookies:
            player_id = int(request.cookies["login_state"].split("-")[1])
    except (ValueError, TypeError, IndexError):
        return await render_template("error.html", error_message="Invalid player ID")

    if player_id is None:
        return await render_template(
            "error.html", error_message="No player ID provided"
        )

    p = glob.players.get(id=player_id)
    if not p:
        return await render_template("error.html", error_message="Player not found")

    player_stats = p.stats.as_json

    recent_scores = None

    try:
        recent_scores = await p.get_scores(50)
    except:
        pass
    if not recent_scores:
        recent_scores = []
    for score in recent_scores:
        score.mods = ModList.from_dict(json.loads(score.mods))
        if score.bmap is None:
            continue
        score.link = f"https://osu.ppy.sh/b/{score.bmap.id}"
        score.map_cover = (
            f"https://assets.ppy.sh/beatmaps/{score.bmap.set_id}/covers/cover.jpg"
        )

    top_scores = None

    try:
        top_scores = await p.top_scores(50)
    except:
        pass
    if not top_scores:
        top_scores = []
    for score in top_scores:
        score.mods = ModList.from_dict(json.loads(score.mods))
        if score.bmap is None:
            continue
        score.map_link = f"https://osu.ppy.sh/b/{score.bmap.id}"
        score.map_cover = (
            f"https://assets.ppy.sh/beatmaps/{score.bmap.set_id}/covers/cover.jpg"
        )

    level = 0

    def level_formula(i):
        try:
            if i >= 100:
                return 26931190827 + 99999999999 * (i - 100)
            return int((5000 / 3 * (4 * i**3 - 3 * i**2 - i)) + 1.25 ** (i - 60))
        except ZeroDivisionError:
            return 0

    i = 1
    while True:
        cur = level_formula(i)
        nxt = level_formula(i + 1)
        if cur <= int(player_stats["rscore"]) and nxt >= int(player_stats["rscore"]):
            level = i
            break
        i += 1
        if cur > int(player_stats["rscore"]) and nxt > int(player_stats["rscore"]):
            level = i
            break

    player_stats["acc"] = f"{player_stats['acc']:.2f}%"
    player_stats["rscore"] = int(player_stats["rscore"])

    avatar = f"/user/avatar/{player_id}.png"
    return await render_template(
        "profile.html",
        player_stats=player_stats,
        recent_scores=recent_scores,
        top_scores=top_scores,
        player=p,
        level=level,
        avatar_url=avatar,
    )
