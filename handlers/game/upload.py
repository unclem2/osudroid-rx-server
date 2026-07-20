
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

<<<<<<< HEAD:handlers/game/upload.py
    path = f"{config.replays_folder}{replay_id}.odr"
=======
    path = f"/srv/odrx_storage/dev/replays/{replay_id}.odr"
>>>>>>> 0384a5e50aa8acb4edffaf39ae3958fd60bcf085:handlers/cho/upload.py
    raw_replay = await file.read()

    if raw_replay[:2] != b"PK":
        return Failed("Fuck off lol.")

    if pathlib.Path(path).is_file():
        return Failed("File already exists.")

    pathlib.Path(path).write_bytes(raw_replay)

    return Success("Replay uploaded.")
