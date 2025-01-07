from quart import Blueprint
from objects import glob
import os

bp = Blueprint('get_online', __name__)

@bp.route('/')
async def get_online():
    online_players = [_ for _ in glob.players if _.online]
    return {'online': len(online_players)}

