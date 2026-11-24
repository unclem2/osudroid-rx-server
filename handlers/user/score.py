from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.services import get_beatmap_service, get_player_service, get_score_service
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService
from objects.services.score import ScoreService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("", name="score")
async def score_details(
    request: Request,
    id: int = Query(...),
    score_service: ScoreService = Depends(get_score_service),
    beatmap_service: BeatmapService = Depends(get_beatmap_service),
    player_service: PlayerService = Depends(get_player_service),
):
    score_id = id
    score = await score_service.from_id(score_id)
    if not score:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error_message": "Score not found"},
        )

    beatmap = await beatmap_service.from_md5_api(score.md5)
    if beatmap is None:
        beatmap = await beatmap_service.from_md5(score.md5)

    if beatmap:
        score.beatmap = beatmap

    player = await player_service.from_uid(score.player_id)

    return templates.TemplateResponse(
        request,
        "score.html",
        {
            "score": score,
            "beatmap": beatmap,
            "player": player,
        },
    )
