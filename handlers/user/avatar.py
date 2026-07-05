from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/avatar"


@router.get("/{uid}.png")
async def avatar(uid: int):
    user_avatar = Path(f"/srv/odrx_storage/dev/avatar/{uid}.png")
    if not user_avatar.exists():
        user_avatar = Path("/srv/odrx_storage/dev/avatar/default.png")

    return FileResponse(user_avatar, media_type="image/png")
