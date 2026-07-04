import os

from fastapi import APIRouter, Request

from handlers.response import Failed, Success

router = APIRouter()

php_file = True


@router.post("")
async def upload_replay(request: Request):
    form = await request.form()

    file = form.get("uploadedfile")
    replay_id = form.get("replayID")

    path = f"data/replays/{replay_id}.odr"
    raw_replay = await file.read()

    if raw_replay[:2] != b"PK":
        return Failed("Fuck off lol.")

    if os.path.isfile(path):
        return Failed("File already exists.")

    with open(path, "wb") as f:
        f.write(raw_replay)

    return Success("Replay uploaded.")
