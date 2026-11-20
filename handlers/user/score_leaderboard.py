from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from osudroid_api_wrapper import ModList

from objects.dependencies.services import get_score_service
from objects.services.score import ScoreService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("")
async def score_leaderboard(
    request: Request,
    mods: str | None = None,
    score_service: ScoreService = Depends(get_score_service),
):
    selected_mods = [
        mod.strip().upper()
        for mod in (mods or "").split(",")
        if mod.strip()
    ]
    mod_entries = [] if "NM" in selected_mods else [
        {"acronym": mod}
        for mod in selected_mods
    ]
    modlist = ModList.from_dict(mod_entries) if mods is not None else None

    top_scores = await score_service.global_top_scores(
        100,
        modlist,
    )

    return templates.TemplateResponse(
        request,
        "score_leaderboard.html",
        {
            "top_scores": top_scores,
            "selected_mods": selected_mods,
        },
    )
