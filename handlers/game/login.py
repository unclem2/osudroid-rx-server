import logging
import pathlib
import time

import geoip2.database
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Request

import utils
from config import Config
from handlers.response import Failed, Success
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

ph = PasswordHasher()
router = APIRouter()

php_file = True


@router.post("")
async def login(request: Request, player_service: PlayerService = Depends(get_player_service), config: Config = Depends(get_config)):
    form = await request.form()

    if "username" not in form or len(str(form["username"])) == 0:
        return Failed("Invalid username.")

    player = await player_service.from_username(str(form["username"]))
    if not player:
        return Failed("User not found.")
    if int(form["version"]) != int(config.online_version):
        return Failed("This client is outdated")

    if config.maintenance == True:
        return Failed("Maintenance")

    status = await player_service.get_status(player.id)

    # verify password
    if not await player_service.check_password(player.id, form["password"], None):
        return Failed("Invalid password.")

    if status != 0:
        return Failed("Banned.")

    await player_service.set_last_online(player.id, time.time())

    if not await player_service.get_uuid(player.id):
        await player_service.set_uuid(player.id, utils.make_uuid(player.username))


    avatar = f"{config.host}/user/avatar/0.png"
    if pathlib.Path(f"{config.avatars_folder}{player.id}.png").is_file():
        avatar = f"{config.host}/user/avatar/{player.id}.png"


    if player.country is None:
        country = request.headers.get("CF-IPCountry", None)
        if country:
            await player_service.set_country(player.id, country)


    return Success(
        f"{player.id} {await player_service.get_uuid(player.id)} {player.pp_rank} {player.stats.ranked_score} {player.stats.pp} {player.stats.accuracy / 100} {player.username} {avatar}",
    )
