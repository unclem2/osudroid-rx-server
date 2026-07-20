from objects.dependencies.config import get_config
from config import Config
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/avatar"


@router.get("/{uid}.png")
<<<<<<< HEAD
async def avatar(uid: int, config: Config = Depends(get_config)):
    user_avatar = Path(f"{config.avatars_folder}{uid}.png")
    if not user_avatar.exists():
        user_avatar = Path(f"{config.avatars_folder}default.png")
=======
async def avatar(uid: int):
    user_avatar = Path(f"/srv/odrx_storage/dev/avatar/{uid}.png")
    if not user_avatar.exists():
        user_avatar = Path("/srv/odrx_storage/dev/avatar/default.png")
>>>>>>> 0384a5e50aa8acb4edffaf39ae3958fd60bcf085

    return FileResponse(user_avatar, media_type="image/png")
