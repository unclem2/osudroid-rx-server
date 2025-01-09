from quart import Blueprint, send_file
import os
from handlers.response import Failed

bp = Blueprint("download_replay", __name__)

forced_route = "/api/upload/<string:replay_path>"


@bp.route("/", methods=["GET"])
async def view_replay(replay_path: str):
    path = f"data/replays/{replay_path}"  # already have .odr

    if not os.path.isfile(path):
        return Failed("Replay not found.")

    return await send_file(path)
