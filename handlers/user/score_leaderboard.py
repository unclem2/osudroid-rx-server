from osudroid_api_wrapper.classes.base.modlist import ModList
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from objects.dependencies.mods import get_mod_entries, get_modlist
from objects.dependencies.services import get_score_service
from objects.services.score import ScoreService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("")
async def score_leaderboard(
    request: Request,
    modlist: ModList=Depends(get_modlist),
    score_service: ScoreService = Depends(get_score_service),
):
    selected_mods = [mod.acronym.upper() for mod in modlist.mods] if modlist and modlist.mods else []

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
