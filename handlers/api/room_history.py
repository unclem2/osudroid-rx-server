from quart import Blueprint, request, jsonify, render_template
from objects import glob
from objects.room import read_room_log

bp = Blueprint("room_history", __name__)

@bp.route("/", methods=["GET"])
async def room_history():
    data = request.args
    room_log = read_room_log(data.get("id"))
    
