from quart import Blueprint, request
import os
from handlers.response import Failed, Success

bp = Blueprint("upload", __name__)

php_file = True


@bp.route("/", methods=["POST"])
async def upload_replay():
    # Use await with request.files and request.form for asynchronous access
    files = await request.files
    form = await request.form

    # Correctly access the file and replayID
    file = files.get("uploadedfile")
    replay_id = form.get("replayID")

    path = f"data/replays/{replay_id}.odr"  # doesnt have .odr
    raw_replay = file.read()

    if raw_replay[:2] != b"PK":
        return Failed("Fuck off lol.")

    if os.path.isfile(path):
        return Failed("File already exists.")

    with open(path, "wb") as file:
        file.write(raw_replay)

    return Success("Replay uploaded.")
