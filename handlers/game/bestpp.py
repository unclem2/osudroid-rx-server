from objects.dependencies.config import get_config
from config import Config
import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from handlers.response import Failed

router = APIRouter()

forced_route = "/api/bestpp"


@router.get("/{replay_path}")
async def view_replay(replay_path: str, config: Config = Depends(get_config)):
    replays_dir = os.path.realpath(config.replays_folder)
    path = os.path.realpath(os.path.join(replays_dir, replay_path))

    if not path.startswith(replays_dir + os.sep) and path != replays_dir:
        return Failed("Invalid replay path.")

    if not os.path.isfile(path):
        return Failed("Replay not found.")

    return FileResponse(path)
