from objects.dependencies.config import get_config
from fastapi import APIRouter, Depends
from config import Config

router = APIRouter()

forced_route = "/api/game/banner.php"


@router.get("", include_in_schema=False)
async def send_banner(config: Config = Depends(get_config)):
    data = {
        "Url": config.banner_url,
        "ImageLink": f"{config.host}/static/banner.png",
    }
    return f"{data}"
