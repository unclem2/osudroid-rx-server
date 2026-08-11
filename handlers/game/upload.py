
import os
import pathlib

from fastapi import APIRouter, Depends, Request

from config import Config
from handlers.response import Failed, Success
from objects.dependencies.config import get_config

router = APIRouter()

php_file = True


@router.post("")
async def upload_replay(request: Request, config: Config = Depends(get_config)):
    form = await request.form()

    file = form.get("uploadedfile")
    replay_id = form.get("replayID")

    if not replay_id or not str(replay_id).isdigit():
        return Failed("Invalid replay ID.")

    replays_dir = os.path.realpath(config.replays_folder)
    path = os.path.realpath(os.path.join(replays_dir, f"{replay_id}.odr"))

    if not path.startswith(replays_dir + os.sep):
        return Failed("Invalid replay path.")

    raw_replay = await file.read()

    if raw_replay[:2] != b"PK":
        return Failed("Fuck off lol.")

    if pathlib.Path(path).is_file():
        return Failed("File already exists.")

    pathlib.Path(path).write_bytes(raw_replay)

    return Success("Replay uploaded.")
