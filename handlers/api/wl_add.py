from quart import Blueprint, request
from objects import glob
from objects.beatmap import Beatmap
import os

bp = Blueprint('wl_add', __name__)

@bp.route('/', methods=['GET'])
async def whitelist_add():
    data = request.args
    if data.get('key') != os.getenv("WL_KEY"):
        return {'status': 'error', 'message': 'Key not specified or incorrect.'}
    if data.get('md5') is not None:
        map = await Beatmap.from_md5(data.get('md5'))
    if data.get('bid') is not None:
        map = await Beatmap.from_bid_osuapi(data.get('bid'))
    if map is None:
        return {'status': 'error', 'message': 'Map not exist'}
    await map.download()
    await glob.db.execute("UPDATE maps SET status = 5 WHERE id = $1", [map.id])
    map_data = {
        "title": f"{map.artist} - {map.title} ({map.creator}) [{map.version}]",
        "md5": map.md5,
        "stats": f"CS: {map.cs} AR: {map.ar} OD: {map.od} HP: {map.hp} BPM: {map.bpm} Stars: {map.star}",
        "status": map.status
    }

    return map_data