from quart import Blueprint, request, jsonify, render_template
from objects import glob
from objects.room import read_room_log

bp = Blueprint("room_history", __name__)


@bp.route("/", methods=["GET"])
async def room_history():
    data = request.args
    room_log = read_room_log(data.get("id"))
    out_type = data.get("type")
    new_data = []

    if out_type == "match":
        room_match = {}
        for i in room_log:
            if (
                i["event"] == "beatmapChanged"
                and i["direction"] == "out"
                and i["data"] != {}
            ):
                room_match["map_hash"] = i["data"]["md5"]
                room_match[
                    "map_name"
                ] = f"{i['data']['artist']} - {i['data']['title']} ({i['data']['creator']}) [{i['data']['version']}]"
            elif i["event"] == "allPlayersScoreSubmitted":
                room_match["scores"] = i["data"]
                new_data.append(room_match)
                room_match = {}

    return jsonify(new_data)
