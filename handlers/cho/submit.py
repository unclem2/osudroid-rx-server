from quart import Blueprint, request
import logging
import time
from objects import glob
from handlers.response import Failed, Success
from objects.score import Score, SubmissionStatus
from objects.beatmap import RankedStatus
import utils
import geoip2.database
import os
from objects.player import Player

bp = Blueprint("submit", __name__)

php_file = True


@bp.route("/", methods=["POST"])
async def submit_play():
    params = await request.form
    if "userID" not in params:
        return Failed("Not enough argument.")

    player: Player = glob.players.get(id=int(params["userID"]))
    player.last_online = time.time()
    if not player:
        return Failed("Player not found, report to server admin.")

    if "ssid" in params:
        if params["ssid"] != player.uuid:
            return Failed("Server restart, please relogin.")

    if glob.config.disable_submit:
        return Failed("Score submission is disable right now.")

    if md5 := params.get("hash", None):
        logging.info(f"Changed {player} playing to {md5}")
        player.stats.playing = md5
        if glob.config.legacy == True:
            return Success(1, player.id)

    if play_data := params.get("data"):
        score: Score = await Score.from_submission(play_data)
        if not score:
            return Failed("Failed to read score data.")

        if score.status == SubmissionStatus.BEST:
            await glob.db.execute(
                "UPDATE scores SET status = 1 WHERE status = 2 AND md5 = $1 AND playerID = $2",
                [score.md5, score.player.id],
            )

        if score.md5 == None:
            return Failed("Server cannot find your recent play, maybe it restarted?")

        if not score.player:
            return Failed("Player not found, report to server admin.")

        if not score.bmap:
            return Success(score.player.stats.droid_submit_stats)

        if score.bmap.status == RankedStatus.Pending:
            return Success(score.player.stats.droid_submit_stats)

        vals = [
            score.status,
            score.md5,
            score.player.id,
            score.score,
            score.max_combo,
            score.grade,
            score.acc,
            score.h300,
            score.hgeki,
            score.h100,
            score.hkatsu,
            score.h50,
            score.hmiss,
            score.mods,
            score.pp.calc_pp,
            score.bmap.id,
            score.date,
            score.local_placement,
            score.global_placement if score.local_placement == 1 else 0,
        ]
        score.id = await glob.db.execute(
            """
            INSERT INTO scores (status, md5, playerID, score, combo, grade, acc, hit300, hitgeki, hit100, hitkatsu, hit50, hitmiss, mods, pp, mapid, date, local_placement, global_placement)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        """,
            vals,
        )

        upload_replay = False
        if score.status == SubmissionStatus.BEST:
            upload_replay = True

        stats = score.player.stats
        stats.plays += 1
        stats.tscore = score.score

        if score.status == SubmissionStatus.BEST and score.bmap.gives_reward:
            additive = score.score
            if score.prev_best:
                additive -= score.prev_best.score
            stats.rscore += additive

        await glob.db.execute(
            "UPDATE stats SET rscore = $1, tscore = $2, plays = $3 WHERE id = $4",
            [stats.rscore, stats.tscore, stats.plays, score.player.id],
        )

        await score.player.update_stats()
        await utils.send_webhook(
            title="New score was submitted",
            content=f"{score.player.username}  | {score.bmap.full} {score.mods} {round(score.acc, 2)}% {score.max_combo}x/{score.bmap.max_combo}x {score.hmiss}x #{score.global_placement} | {round(score.pp.calc_pp, 2)}",
            url=glob.config.submit_hook,
            isEmbed=True,
        )
        if glob.config.legacy == True:
            return Success(
                "{rank} {legacy_metric} {acc} {map_rank} {score_id}".format(
                    rank=int(stats.pp_rank if glob.config.pp else stats.score_rank),
                    legacy_metric=int(stats.pp if glob.config.pp else stats.rscore),
                    acc=stats.droid_acc,
                    map_rank=score.global_placement,
                    score_id=score.id if upload_replay else "",
                )
            )
        else:
            files = await request.files

            # Correctly access the file and replayID
            file = files.get("replayFile")
            replay_id = score.id

            path = f"data/replays/{replay_id}.odr"  # doesnt have .odr
            raw_replay = file.read()

            if raw_replay[:2] != b"PK":
                return Failed("Fuck off lol.")

            if os.path.isfile(path):
                return Failed("File already exists.")

            with open(path, "wb") as file:
                file.write(raw_replay)
            return Success(
                "{rank} {score} {acc} {map_rank} {pp}".format(
                    rank=int(stats.pp_rank if glob.config.pp else stats.score_rank),
                    score=stats.rscore,
                    acc=stats.droid_acc,
                    map_rank=score.global_placement,
                    pp=stats.pp,
                )
            )

    return Failed("Huh?")
