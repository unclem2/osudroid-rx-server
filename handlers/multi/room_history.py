# from quart import Blueprint, request, jsonify, render_template
# from objects import glob
# from objects.room import read_room_log

# bp = Blueprint("room_history", __name__)

# @bp.route("/", methods=["GET"])
# async def room_history():
#     data = request.args
#     room_log = read_room_log(data.get("id"))
#     cleaned_log = []
#     for entry in room_log:
#         if entry["event"] == "playerStatusChanged":
#             new_entry = {
#                 "event": entry["event"],
#                 "time": entry["time"],
#                 "data": {
#                     "uid": entry["data"][0],
#                     "status": entry["data"][1],
#                 },
#             }
#             cleaned_log.append(new_entry)
