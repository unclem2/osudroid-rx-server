
import pathlib

from fastapi import APIRouter, Depends, Request

from config import Config
from handlers.response import Failed, Success
from objects.dependencies.config import get_config
from objects.dependencies.services import get_score_service
from objects.services.score import ScoreService

router = APIRouter()

php_file = True


@router.post("")
async def leaderboard(request: Request, score_service: ScoreService = Depends(get_score_service), config: Config = Depends(get_config)):
    form = await request.form()
    res = []

    if "hash" not in form:
        return Failed("No map hash.")

    scores = await score_service.beatmap_scores(form["hash"], order_by=form["type"])
    for score in scores or []:

        if pathlib.Path(f"data/avatar/{score.player.id}.png").is_file():
            avatar = f"{config.host}/user/avatar/{score.player.id}.png"
        else:
            avatar = f"{config.host}/user/avatar/0.png"

        formatted = (
            f"{score.id} {score.player.username} {score.score} "
            f"{round(score.pp)} {score.max_combo} {score.grade} "
            f"{score.mods.as_json_string} {round(float(score.accuracy / 100), 4)} {avatar}"
        )

        res += [formatted]

    return Success("\n".join(res))
