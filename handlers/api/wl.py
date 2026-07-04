from fastapi import APIRouter
from fastapi.responses import JSONResponse
from objects import glob
from .models.responses import WhitelistResponse

router = APIRouter()


@router.get("", response_model=WhitelistResponse)
async def whitelist():
    maps = await glob.db.fetchall("SELECT * FROM maps WHERE status = 5")
    return JSONResponse(content=maps)
