import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from handlers.response import Failed

router = APIRouter()

forced_route = "/api/bestpp"


@router.get("/{replay_path}")
async def view_replay(replay_path: str):
    path = f"data/replays/{replay_path}"

    if not os.path.isfile(path):
        return Failed("Replay not found.")

    return FileResponse(path)
