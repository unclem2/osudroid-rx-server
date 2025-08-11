from quart import Blueprint, request, jsonify
from objects import glob
from objects.beatmap import Beatmap
from objects.room import (
    Room,
    PlayerMulti,
    get_id,
)
from handlers.multi import sio
from handlers.multi.main_namespace import MultiNamespace


bp = Blueprint("createroom", __name__)


@bp.route("/", methods=["POST"])
async def create_room():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    room_id = get_id()
    room = Room()
    room.id = room_id
    room.name = data["name"]
    room.maxPlayers = data["maxPlayers"]
    room.host = PlayerMulti().player(int(data["host"]["uid"]), sid="")
    beatmap_md5 = data["beatmap"]["md5"]
    room.map = await Beatmap.from_md5(beatmap_md5)
    if room.map is not None:
        room.map.md5 = beatmap_md5
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
        room.isLocked = True
    glob.rooms[room_id] = room

    response = {"id": room.id}
    sio.register_namespace(MultiNamespace(f"/multi/{room.id}"))
    return f"{response}"
