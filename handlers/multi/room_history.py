from quart import Blueprint, request, jsonify, render_template
from objects import glob
from objects.room.utils import read_room_log

bp = Blueprint("room_history", __name__)


@bp.route("/", methods=["GET"])
async def room_history():
    data = request.args
    room_log = read_room_log(data.get("id"))
    ret = []
    current_beatmap = None
    for i, record in enumerate(room_log):
        if record["direction"] == "in":
            continue
        if record["event"] == "beatmapChanged":
            current_beatmap = record["data"]
        elif record["event"] == "allPlayersScoreSubmitted":
            ret.append(
                {"event": "match", "beatmap": current_beatmap, "scores": record["data"]}
            )

    return jsonify(ret)
