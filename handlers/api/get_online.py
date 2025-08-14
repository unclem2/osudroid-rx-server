from quart import Blueprint
from objects import glob
from handlers.response import ApiResponse
from quart_schema import validate_response

bp = Blueprint("get_online", __name__)


@bp.route("/")
@validate_response(ApiResponse[int], 200)
async def get_online():
    """
    Get the number of online players.
    """
    online_players = [_ for _ in glob.players if _.online]
    return ApiResponse.ok(len(online_players))
