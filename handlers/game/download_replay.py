
import pathlib

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from config import Config
from handlers.response import Failed
from objects.dependencies.config import get_config

router = APIRouter()

forced_route = "/api/upload"


@router.get("/{replay_path}")
async def view_replay(replay_path: str, config: Config = Depends(get_config)):
    path = f"{config.replays_folder}{replay_path}"

    if not pathlib.Path(path).is_file():
        return Failed("Replay not found.")

    return FileResponse(path)
