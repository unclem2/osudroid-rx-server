from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from objects import glob
from objects.room.utils import read_room_log

router = APIRouter()


@router.get("")
async def room_history(request: Request):
    room_id = request.query_params.get("id")
    room_log = read_room_log(room_id)
    ret = []
    current_beatmap = None
    for i, record in enumerate(room_log):
        if record["direction"] == "in":
            continue
        if record["event"] == "beatmapChanged":
            current_beatmap = record["data"]
        elif record["event"] == "allPlayersScoreSubmitted":
            ret.append(
                {
                    "event": "match",
                    "beatmap": current_beatmap,
                    "scores": record["data"],
                }
            )

    return JSONResponse(content=ret)
