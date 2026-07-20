from fastapi import APIRouter, Depends
from pydantic import BaseModel

from config import Config
from objects.dependencies.config import get_config

router = APIRouter()

php_file = True


class UpdateInfo(BaseModel):
    version_code: int
    link: str
    changelog: str


class UpdateResponse(BaseModel):
    status: str = "success"
    data: UpdateInfo


@router.get("")
async def send_update(config: Config = Depends(get_config)):
    data = {
        "version_code": config.client_version_code,
        "link": config.client_link,
        "changelog": config.client_changelog,
    }
    return f"{data}"
