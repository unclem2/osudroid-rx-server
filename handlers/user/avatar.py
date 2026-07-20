from objects.dependencies.config import get_config
from config import Config
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/avatar"


@router.get("/{uid}.png")
async def avatar(uid: int, config: Config = Depends(get_config)):
    user_avatar = Path(f"{config.avatars_folder}{uid}.png")
    if not user_avatar.exists():
        user_avatar = Path(f"{config.avatars_folder}default.png")

    return FileResponse(user_avatar, media_type="image/png")
