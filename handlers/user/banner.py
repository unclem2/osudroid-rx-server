from objects.dependencies.config import get_config
from config import Config
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

router = APIRouter()

forced_route = "/user/banner"


@router.get("/{uid}.png")
<<<<<<< HEAD
async def banner(uid: int, config: Config = Depends(get_config)):
    user_banner = Path(f"{config.banners_folder}{uid}.png")
    if not user_banner.exists():
        user_banner = Path(f"{config.banners_folder}default.png")
=======
async def banner(uid: int):
    user_banner = Path(f"/srv/odrx_storage/dev/banner/{uid}.png")
    if not user_banner.exists():
        user_banner = Path("/srv/odrx_storage/dev/banner/default.png")
>>>>>>> 0384a5e50aa8acb4edffaf39ae3958fd60bcf085

    return FileResponse(user_banner, media_type="image/png")
