from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from objects import glob
from objects.beatmap import Beatmap
from objects.room.room import Room
from objects.room.player import PlayerMulti
from objects.room.utils import get_id
from handlers.multi import sio
from handlers.multi.main_namespace import MultiNamespace

router = APIRouter()


@router.post("")
async def create_room(request: Request):
    data = await request.json()
    if not data:
        return JSONResponse(content={"error": "Invalid request"}, status_code=400)

    room_id = get_id()
    room = Room()
    room.id = room_id
    room.name = data["name"]
    room.max_players = data["maxPlayers"]
    room.host = PlayerMulti.player(int(data["host"]["uid"]), sid="")
    beatmap_md5 = data["beatmap"]["md5"]
    beatmap_obj = await Beatmap.from_md5(beatmap_md5)
    if beatmap_obj is not None:
        beatmap_obj.md5 = beatmap_md5
        room.map = beatmap_obj
    else:
        beatmap = data.get("beatmap", {})
        room.map = Beatmap()
        room.map.title = beatmap.get("title", "")
        room.map.artist = beatmap.get("artist", "")
        room.map.version = beatmap.get("version", "")
        room.map.creator = beatmap.get("creator", "")
        room.map.md5 = beatmap_md5
    if "password" in data:
        room.password = data["password"]
        room.is_locked = True
    glob.rooms.add(room)

    response = {"id": room.id}
    sio.register_namespace(MultiNamespace(f"/multi/{room.id}"))
    return f"{response}"
