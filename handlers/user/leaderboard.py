from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_player_service
from objects.services.player import PlayerService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


PER_PAGE = 50

STAT_LABELS = {
    "pp": "PP",
    "score": "Ranked Score",
    "playcount": "Play Count",
    "accuracy": "Accuracy",
    "h300": "300",
    "h100": "100",
    "h50": "50",
    "hmiss": "Miss",
    "rank_xh": "XH",
    "rank_x": "X",
    "rank_sh": "SH",
    "rank_s": "S",
    "rank_a": "A",
    "rank_b": "B",
    "rank_c": "C",
    "rank_d": "D",
}


@router.get("")
async def leaderboard(
    request: Request,
    player_service: PlayerService = Depends(get_player_service),
):
    sortby = request.query_params.get("sortby", "pp").lower()
    country = request.query_params.get("country", "").upper()
    search = request.query_params.get("search", "").strip()
    valid_sortby = {
        "score", "pp", "playcount", "accuracy", "h300", "h100", "h50", "hmiss",
        "rank_xh", "rank_x", "rank_sh", "rank_s", "rank_a", "rank_b", "rank_c", "rank_d",
    }
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
        all_players = await player_service.list_from_query(sortby, country_filter, limit, offset, search_lower)
        total = len(all_players)
        total_pages = max(1, -(-total // limit))
        current_page = (offset // limit) + 1
        current_page = max(1, min(current_page, total_pages))
        offset = (current_page - 1) * limit
        players = all_players[offset:offset + limit]
    else:
        total = await player_service.get_leaderboard_count(sortby, country_filter)
        total_pages = max(1, -(-total // limit))
        current_page = (offset // limit) + 1
        current_page = max(1, min(current_page, total_pages))
        offset = (current_page - 1) * limit
        players = await player_service.get_leaderboard(sortby, country_filter, limit, offset)

    stat_values = {}
    stat_ranks = {}
    for player in players:
        if sortby in {"pp", "score"}:
            stat_values[player.id] = round(player.stats.pp, 2) if sortby == "pp" else player.stats.ranked_score
            stat_ranks[player.id] = player.pp_rank if sortby == "pp" else player.score_rank
        elif sortby in {"playcount", "accuracy"}:
            stat_values[player.id] = round(player.stats.accuracy, 2) if sortby == "accuracy" else player.stats.playcount
            stat_ranks[player.id] = getattr(player.stats, f"{sortby}_rank")
        elif sortby == "h300":
            stat_values[player.id] = player.stats.h300 + player.stats.hgeki
            stat_ranks[player.id] = player.stats.h300_rank
        elif sortby == "h100":
            stat_values[player.id] = player.stats.h100 + player.stats.hkatsu
            stat_ranks[player.id] = player.stats.h100_rank
        else:
            stat_values[player.id] = getattr(player.stats, sortby)
            stat_ranks[player.id] = getattr(player.stats, f"{sortby}_rank")

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
            "stat_labels": STAT_LABELS,
            "stat_values": stat_values,
            "stat_ranks": stat_ranks,
        },
    )
