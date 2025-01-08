from quart import Blueprint, request
from objects import glob

bp = Blueprint("get_user", __name__)


@bp.route("/")
async def get_user():
    args = request.args

    if "id" not in args and "name" not in args:
        return "Need id or name", 400

    if "id" in args:
        if not args["id"].isdecimal():
            return "Invalid id", 400

        player = glob.players.get(id=int(args["id"]))
    else:
        if len(args["name"]) < 2:
            return "Invalid name", 400

        player = glob.players.get(name=args["name"])

    if not player:
        return "Player not found", 404

    return player.as_json
