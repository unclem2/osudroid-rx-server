
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_player_service, get_score_service
from objects.services.player import PlayerService
from objects.services.score import ScoreService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("")
async def profile(request: Request, player_service: PlayerService = Depends(get_player_service), score_service: ScoreService = Depends(get_score_service)):
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

    recent_scores = await score_service.player_scores(player.id, "all", limit=100)

    top_scores = await score_service.player_top_scores(player_id)

    first_place_scores = await score_service.player_first_places(player_id, order_by="date")

    avatar = f"/user/avatar/{player_id}.png"
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "player_stats": player.stats,
            "recent_scores": recent_scores,
            "top_scores": top_scores,
            "first_place_scores": first_place_scores,
            "player": player,
            "level": player.stats.level,
            "avatar_url": avatar,
        },
    )
