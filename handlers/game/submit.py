import logging
import pathlib
import time

from fastapi import APIRouter, Depends, Request

import utils
from config import Config
from handlers.response import Failed, Success
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service, get_score_service
from objects.services.player import PlayerService
from objects.services.score import ScoreService

router = APIRouter()

php_file = True


@router.post("")
async def submit_play(request: Request, config: Config = Depends(get_config), player_service: PlayerService = Depends(get_player_service), score_service: ScoreService = Depends(get_score_service)):
    form = await request.form()
    if "userID" not in form:
        return Failed("Not enough argument.")

    player = await player_service.from_uid(int(form["userID"]))
    if not player:
        return Failed("Player not found, report to server admin.")

    await player_service.set_last_online(player.id, time.time())

    if "ssid" in form and form["ssid"] != await player_service.get_uuid(player.id):
        return Failed("Server restart, please relogin.")

    if config.disable_submit:
        return Failed("Score submission is disable right now.")

    if md5 := form.get("hash", None):
        logging.info("Changed %s playing to %s", player, md5)
        await player_service.set_playing(player.id, md5)

    if play_data := form.get("data"):
        score = await score_service.from_submit(play_data)
        if not score:
            return Failed("Failed to read score data.")

        score = await score_service.save(score)
        await utils.send_webhook(
            title="New score was submitted",
            content=f"{score.player.username}  | {score.beatmap.full} {score.mods.as_standard_mods} {round(score.accuracy, 2)}% {score.max_combo}x/{score.beatmap.max_combo}x {score.hmiss}x # | {round(score.pp, 2)}",
            url=config.submit_hook,
            isEmbed=True,
        )

        await player_service.update_stats(player)

        file = form.get("replayFile")
        replay_id = score.id

        path = f"{config.replays_folder}{replay_id}.odr"
        raw_replay = await file.read()

        if raw_replay[:2] != b"PK":
            return Failed("Fuck off lol.")

        if pathlib.Path(path).is_file():
            return Failed("File already exists.")

        pathlib.Path(path).write_bytes(raw_replay)
        return Success(
            f"{int(player.pp_rank)} {player.stats.ranked_score} {player.stats.accuracy / 100} {await score_service.score_global_placement(score)} {player.stats.pp}",
        )

    return Failed("Huh?")
