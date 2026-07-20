from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from config import Config
from objects.dependencies.config import get_config
from objects.dependencies.services import get_player_service, get_score_service
from objects.services.player import PlayerService
from objects.services.score import ScoreService

templates = Jinja2Templates(directory="templates")


forced_route = ""

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index(request: Request, config: Config = Depends(get_config), player_service: PlayerService = Depends(get_player_service), score_service: ScoreService = Depends(get_score_service)):
    title = config.server_name
    changelog = config.client_changelog
    version = config.client_version
    download_link = config.client_link

    top_scores = await score_service.global_top_scores(10)

    return templates.TemplateResponse(
        request,
        "main_page.html",
        {
            "players": await player_service.get_online_players_count(),
            "online": await player_service.get_player_count(),
            "title": title,
            "changelog": changelog,
            "download_link": download_link,
            "version": version,
            "top_scores": top_scores,
        },
    )
