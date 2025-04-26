from quart import Blueprint, request, jsonify
from objects import glob

bp = Blueprint("getrooms", __name__)


@bp.route("/")
async def get_rooms():
    room = []
    for room_id, room_info in glob.rooms.items():
        players = ",".join([player.username for player in room_info.players])

        room.append(
            {
                "id": room_info.id,
                "name": room_info.name,
                "isLocked": room_info.isLocked,
                "gameplaySettings": room_info.gameplaySettings.as_json(),
                "maxPlayers": room_info.maxPlayers,
                "mods": room_info.mods.as_json(),
                "playerNames": players,
                "playerCount": len(room_info.players),
                "status": room_info.status,
                "teamMode": room_info.teamMode,
                "winCondition": room_info.winCondition,
            }
        )

    return jsonify(room)
