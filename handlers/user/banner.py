from objects.dependencies.config import get_config
from config import Config
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/banner"


@router.get("/{uid}.png")
async def banner(uid: int, config: Config = Depends(get_config)):
    user_banner = Path(f"{config.banners_folder}{uid}.png")
    if not user_banner.exists():
        user_banner = Path(f"{config.banners_folder}default.png")

    return FileResponse(user_banner, media_type="image/png")
