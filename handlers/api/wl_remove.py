from quart import Blueprint, request
import os
from objects import glob

bp = Blueprint("wl_remove", __name__)


@bp.route("/", methods=["GET"])
async def whitelist_remove():
    data = request.args
    if data.get("key") != glob.config.wl_key:
        return {"status": "error", "message": "Key not specified or incorrect."}
    if data.get("md5") is not None:
        await glob.db.execute(
            "UPDATE maps SET status = -2 WHERE md5 = $1", [data.get("md5")]
        )
    elif data.get("bid") is not None:
        if not data.get("bid").isdecimal():
            return {"status": "error", "message": "Invalid beatmap id."}
        await glob.db.execute(
            "UPDATE maps SET status = -2 WHERE id = $1", [int(data.get("bid"))]
        )
    return {"status": "successfully removed from whitelist"}
