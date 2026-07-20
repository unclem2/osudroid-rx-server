from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


PER_PAGE = 50


@router.get("")
async def leaderboard(request: Request, player_service: PlayerService = Depends(get_player_service)):
    sortby = request.query_params.get("sortby", "pp").lower()
    country = request.query_params.get("country", "").upper()
    search = request.query_params.get("search", "").strip()

    valid_sortby = {"score", "pp"}
    if sortby not in valid_sortby:
        sortby = "pp"

    try:
        offset = max(0, int(request.query_params.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0

    try:
        limit = max(1, min(100, int(request.query_params.get("limit", PER_PAGE))))
    except (ValueError, TypeError):
        limit = PER_PAGE

    countries = await player_service.get_countries_list()
    if not countries:
        countries = []

    country_filter = country or None

    if search:
        search_lower = search.lower()
        total_count = await player_service.get_leaderboard_count(sortby, country_filter)
        all_players = await player_service.get_leaderboard(sortby, country_filter, total_count, 0)
        players = [p for p in all_players if search_lower in p.username.lower()]
        total = len(players)
        total_pages = max(1, -(-total // limit))
        current_page = (offset // limit) + 1
        current_page = max(1, min(current_page, total_pages))
        offset = (current_page - 1) * limit
        players = players[offset:offset + limit]
    else:
        total = await player_service.get_leaderboard_count(sortby, country_filter)
        total_pages = max(1, -(-total // limit))
        current_page = (offset // limit) + 1
        current_page = max(1, min(current_page, total_pages))
        offset = (current_page - 1) * limit
        players = await player_service.get_leaderboard(sortby, country_filter, limit, offset)

    return templates.TemplateResponse(
        request,
        "leaderboard.html",
        {
            "leaderboard": players,
            "country": country or None,
            "countries": countries,
            "sortby": sortby,
            "search": search,
            "page": current_page,
            "total_pages": total_pages,
            "offset": offset,
            "limit": limit,
        },
    )
