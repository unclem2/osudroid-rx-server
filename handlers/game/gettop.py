from fastapi import APIRouter, Depends, Request

from handlers.response import Failed, Success
from objects.dependencies.services import get_score_service
from objects.services.score import ScoreService

router = APIRouter()

php_file = True


@router.post("")
async def view_score(request: Request, score_service: ScoreService = Depends(get_score_service)):
    form = await request.form()

    score = await score_service.from_id(int(form["playID"]))
    if score:
        return Success(score.droid_string)

    return Failed("Score not found.")
