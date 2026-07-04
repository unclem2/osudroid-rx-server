from fastapi import APIRouter
from objects import glob

router = APIRouter()

forced_route = "/api/game/banner.php"


@router.get("", include_in_schema=False)
async def send_banner():
    data = {
        "Url": glob.config.banner_url,
        "ImageLink": f"{glob.config.host}/static/banner.png",
    }
    return f"{data}"
