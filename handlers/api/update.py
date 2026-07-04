from fastapi import APIRouter
from pydantic import BaseModel
from objects import glob

router = APIRouter()

php_file = True


class UpdateInfo(BaseModel):
    version_code: int
    link: str
    changelog: str


class UpdateResponse(BaseModel):
    status: str = "success"
    data: UpdateInfo


@router.get("", response_model=UpdateResponse)
async def send_update():
    data = {
        "version_code": glob.config.client_version_code,
        "link": glob.config.client_link,
        "changelog": glob.config.client_changelog,
    }
    return f"{data}"
