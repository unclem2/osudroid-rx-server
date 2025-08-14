from quart import Blueprint, request
from objects import glob
from handlers.response import Failed, Success
import os

bp = Blueprint("gettop", __name__)

php_file = True


@bp.route("/", methods=["POST"])
async def view_score():
    params = await request.form

    play = await glob.db.fetch(
        "SELECT * FROM scores WHERE id = $1", [int(params["playID"])]
    )
    if play:
        return Success(
            "{mods} {score} {combo} {grade} {hitgeki} {hit300} {hitkatsu} {hit100} {hit50} {hitmiss} {acc} {date}".format(
                mods=play["mods"],
                score=(int(play["pp"]) if glob.config.pp_leaderboard else play["score"])
                if glob.config.legacy == True
                else play["score"],
                combo=play["combo"],
                grade=play["grade"],
                hitgeki=play["hitgeki"],
                hit300=play["hit300"],
                hitkatsu=play["hitkatsu"],
                hit100=play["hit100"],
                hit50=play["hit50"],
                hitmiss=play["hitmiss"],
                acc=int(play["acc"] * 1000) if glob.config.legacy == True else "",
                date=play["date"],
            )
        )

    return Failed("Score not found.")
