from quart import Blueprint, request, jsonify
from objects import glob

bp = Blueprint("getrooms", __name__)


@bp.route("/")
async def get_rooms():
    room_list = []
    for room_info in glob.rooms:
        players = ",".join([player.username for player in room_info.players])

        room_list.append(
            {
                "id": room_info.id,
                "name": room_info.name,
                "isLocked": room_info.is_locked,
                "gameplaySettings": room_info.gameplay_settings.as_json,
                "maxPlayers": room_info.max_players,
                "mods": room_info.mods.as_json,
                "playerNames": players,
                "playerCount": len(room_info.players),
                "status": room_info.status,
                "teamMode": room_info.team_mode,
                "winCondition": room_info.win_condition,
            }
        )

    return jsonify(room_list)
