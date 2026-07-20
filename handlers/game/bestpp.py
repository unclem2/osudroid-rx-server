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
    path = f"{config.replays_folder}{replay_path}"

    if not os.path.isfile(path):
        return Failed("Replay not found.")

    return FileResponse(path)
