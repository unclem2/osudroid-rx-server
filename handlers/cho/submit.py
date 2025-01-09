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

    player = glob.players.get(id=int(params["userID"]))
    player.last_online = time.time()
    if not player:
        return Failed("Player not found, report to server admin.")

    if "ssid" in params:
        if params["ssid"] != player.uuid:
            return Failed("Server restart, please relogin.")

    if glob.config.disable_submit:
        return Failed("Score submission is disable right now.")

    if player.country == None:
        if os.path.exists("GeoLite2-Country.mmdb"):
            with geoip2.database.Reader("GeoLite2-Country.mmdb") as reader:
                ip = request.remote_addr
                response = reader.country(ip)
                country = response.country.iso_code
                await glob.db.execute(
                    "UPDATE users SET country = $1 WHERE id = $2", [country, player.id]
                )
                player_new = await Player.from_sql(int(params["userID"]))
                glob.players.add(player_new)
                glob.players.remove(player)

    if map_hash := params.get("hash", None):
        logging.info(f"Changed {player} playing to {map_hash}")
        player.stats.playing = map_hash
        return Success(1, player.id)

    elif play_data := params.get("data"):
        score = await Score.from_submission(play_data)
        if not score:
            return Failed("Failed to read score data.")

        if score.status == SubmissionStatus.BEST:
            await glob.db.execute(
                "UPDATE scores SET status = 1 WHERE status = 2 AND mapHash = $1 AND playerID = $2",
                [score.map_hash, score.player.id],
            )

        if score.map_hash == None:
            return Failed("Server cannot find your recent play, maybe it restarted?")

        if not score.player:
            return Failed("Player not found, report to server admin.")

        if not score.bmap:
            return Success(score.player.stats.droid_submit_stats)

        if score.bmap.status == RankedStatus.Pending:
            return Success(score.player.stats.droid_submit_stats)

        vals = [
            score.status,
            score.map_hash,
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
            score.pp,
            score.bmap.id,
            score.date,
        ]
        score.id = await glob.db.execute(
            """
            INSERT INTO scores (status, mapHash, playerID, score, combo, rank, acc, hit300, hitgeki, hit100, hitkatsu, hit50, hitmiss, mods, pp, mapid, date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
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
        await utils.discord_notify(
            f"{score.player.name}  | {score.bmap.full} {score.mods} {round(score.acc, 2)}% {score.max_combo}x/{score.bmap.max_combo}x {score.hmiss}x #{score.rank} | {round(score.pp, 2)}",
            glob.config.discord_hook,
        )

        return Success(
            "{rank} {rank_by} {acc} {map_rank} {score_id}".format(
                rank=int(stats.rank),
                rank_by=int(stats.rank_by),
                acc=stats.droid_acc,
                map_rank=score.rank,
                score_id=score.id if upload_replay else "",
            )
        )

    return Failed("Huh?")
