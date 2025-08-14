from objects import glob
from quart import Blueprint, request
import os
from handlers.response import Failed, Success

bp = Blueprint("getrank", __name__)

php_file = True


@bp.route("/", methods=["POST"])
async def leaderboard():
    params = await request.form

    if "hash" not in params:
        return Failed("No map hash.")

    res = []
    if glob.config.legacy:
        plays = await glob.db.fetchall(
            "SELECT * FROM scores WHERE md5 = $1 AND status = 2 ORDER BY {order_by} DESC".format(
                order_by="pp" if glob.config.pp_leaderboard else "score"
            ),
            [params["hash"]],
        )
    else:
        order = params["type"]
        plays = await glob.db.fetchall(
            "SELECT * FROM scores WHERE md5 = $1 AND status = 2 ORDER BY {order_by} DESC".format(
                order_by=order
            ),
            [params["hash"]],
        )
    for play in plays if plays else []:
        player = glob.players.get(id=int(play["playerid"]))

        if os.path.isfile(f"data/avatar/{player.id}.png"):
            avatar = f"{glob.config.host}/user/avatar/{player.id}.png"
        else:
            avatar = f"https://s.gravatar.com/avatar/{player.email_hash}"

        res += [
            "{play_id} {username} {score} {pp} {combo} {grade} {mods} {acc} {avatar}".format(
                play_id=play["id"],
                username=player.username,
                score=(
                    round(play["pp"]) if glob.config.pp_leaderboard else play["score"]
                )
                if glob.config.legacy == True
                else play["score"],
                pp=round(play["pp"]) if glob.config.legacy == False else "",
                combo=play["combo"],
                grade=play["grade"],
                mods=play["mods"],
                acc=int(play["acc"] * 1000)
                if glob.config.legacy == True
                else round(float(play["acc"] / 100), 4),
                avatar=avatar,
            )
        ]

    return Success("\n".join(res))
