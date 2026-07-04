from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/banner"


@router.get("/{uid}.png")
async def banner(uid: int):
    user_banner = Path(f"./data/banner/{uid}.png")
    if not user_banner.exists():
        user_banner = Path("./data/banner/default.png")

    return FileResponse(user_banner, media_type="image/png")
