import socketio
from quart import Blueprint, request, jsonify
import json
from objects import glob
from objects.player import Player
from objects.room import Room, PlayerMulti
from objects.beatmap import Beatmap
import utils
bp = Blueprint('multi', __name__)
bp.prefix = '/multi/'
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', engineio_logger=True)


class MultiNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace)
        
    @property
    def room_id(self):
        return self.namespace.split('/')[-1]

    async def on_disconnect(self, sid):
        print(f"Client disconnected: {sid}")
        
    async def on_connect(self, sid, environ, *args):
        print(f"Client connected: {sid}")
        room_info = glob.rooms.get(self.room_id)
        room_info.players.append(PlayerMulti().player(id=args[0]['uid']), sid=sid)
        resp = {
            'id': room_info.id,
            'name': room_info.name,
            'name': room_info.name,
            'beatmap': {
                'md5': room_info.map.md5,
                'title': room_info.map.title,
                'artist': room_info.map.artist,
                'version': room_info.map.version,
                'creator': room_info.map.creator,
                'beatmapSetId': room_info.map.set_id
            },
            'host': room_info.host.as_json(),
            'isLocked': room_info.isLocked,
            'gameplaySettings': room_info.gameplaySettings.as_json(),
            'maxPlayers': room_info.maxPlayers,
            'mods': room_info.mods.as_json(),
            'players': [p.as_json() for p in room_info.players],
            'status': room_info.status,
            'teamMode': room_info.teamMode,
            'winCondition': room_info.winCondition,
            'sessionId': utils.make_uuid() 
        }

        await sio.emit(data=resp, namespace=self.namespace, event='initialConnection')
        
    # @sio.on('playerModsChanged')
    async def on_playerModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                player.mods = args[0]
                data = [player.uid, player.mods]
                await sio.emit(event='playerModsChanged', data=data, namespace=self.namespace)
                break
        
        
# Register the class for the '/multi' namespace





@bp.route('/createroom', methods=['POST'])
async def create_room():
    data = await request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    room_id = str(len(glob.rooms) + 1)  # Simple dynamic ID generation
    room = Room()
    room.id = room_id
    room.name = data['name']
    room.maxPlayers = data['maxPlayers']
    room.host = PlayerMulti().player(int(data['host']['uid']))
    room.map = await Beatmap.from_md5(data['beatmap']['md5'])
    room.map.md5 = data['beatmap']['md5']
    if 'password' in data:
        room.password = data['password']
    glob.rooms[room_id] = room

    response = {
        "id": room.id
    }
    sio.register_namespace(MultiNamespace(f'/multi/{room.id}'))
    return f"{response}"

@bp.route('/getrooms')
async def get_rooms():

    return '[]'
