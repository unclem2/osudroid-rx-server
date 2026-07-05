from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/banner"


@router.get("/{uid}.png")
async def banner(uid: int):
    user_banner = Path(f"/srv/odrx_storage/dev/banner/{uid}.png")
    if not user_banner.exists():
        user_banner = Path("/srv/odrx_storage/dev/banner/default.png")

    return FileResponse(user_banner, media_type="image/png")
