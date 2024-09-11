import socketio
import socketio.namespace
from objects import glob
from objects.player import Player
from objects.room import Room
from objects.beatmap import Beatmap
from objects.score import Score
from quart import Blueprint, request, jsonify



bp = Blueprint('multi', __name__)
bp.prefix = '/multi/'
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')


@bp.route('/createroom')
async def create_room():
    data = await request.get_json()
    if not data:
        return 'Invalid request', 400
    room = Room()
    room.id = glob.rooms.get_next_id()
    room.name = data['name']
    room.slots = data['maxPlayers']
    room.host = glob.players.get(id=data['host']['uid'])
    room.map = await Beatmap.from_md5(data['beatmap']['md5'])
    glob.rooms.add(room)
    return jsonify({'id': room.id})

@bp.route('/getrooms')
async def get_rooms(): 
    return jsonify([room.to_json() for room in glob.rooms])
    