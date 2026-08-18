
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("")
async def profile(request: Request, player_service: PlayerService = Depends(get_player_service)):
    params = request.query_params
    player_id = None
    try:
        if "id" in params:
            player_id = int(params["id"])
        elif "uid" in params:
            player_id = int(params["uid"])
        elif "login_state" in request.cookies:
            player_id = int(request.cookies["login_state"].split("-")[1])
    except (ValueError, TypeError, IndexError):
        return templates.TemplateResponse(request, "error.html", {"error_message": "Invalid player ID"})

    if player_id is None:
        return templates.TemplateResponse(request, "error.html", {"error_message": "No player ID provided"})

    player = await player_service.from_uid(player_id)
    if not player:
        return templates.TemplateResponse(request, "error.html", {"error_message": "Player not found"})

    avatar = f"/user/avatar/{player_id}.png"
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "player": player,
            "player_stats": player.stats,
            "level": player.stats.level,
            "avatar_url": avatar,
        },
    )
