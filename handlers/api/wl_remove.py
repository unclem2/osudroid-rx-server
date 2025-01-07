from quart import Blueprint, request
import os
from objects import glob

bp = Blueprint('wl_remove', __name__)


@bp.route('/', methods=['GET'])
async def whitelist_remove():
    data = request.args
    if data.get('key') != os.getenv("WL_KEY"):
        return {'status': 'error', 'message': 'Key not specified or incorrect.'}
    if data.get('md5') is not None:
        await glob.db.execute('UPDATE maps SET status = -2 WHERE md5 = $1', [data.get('md5')])
    if data.get('bid') is not None:
        await glob.db.execute('UPDATE maps SET status = -2 WHERE id = $1', [int(data.get('bid'))])
    return {'status': 'success'}
