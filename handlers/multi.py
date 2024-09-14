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
        room_info = glob.rooms.get(self.room_id)
        for i in range(len(room_info.players)):
            if room_info.players[i].sid == sid:
                room_info.players.pop(i)
                break
        if len(room_info.players) == 0:
            glob.rooms.pop(self.room_id)
        
    async def on_connect(self, sid, environ, *args):
        print(f"Client connected: {sid}")
        room_info = glob.rooms.get(self.room_id)
        room_info.players.append(PlayerMulti().player(id=args[0]['uid'], sid=sid))
        
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
                print("aa")
                player.mods.mods = args[0]['mods']
                player.mods.speedMultiplier = args[0]['speedMultiplier']
                player.mods.flFollowDelay = args[0]['flFollowDelay']
                try:
                    player.mods.customAR = args[0].get('customAR', 0)
                    player.mods.customOD = args[0].get('customOD', 0)
                    player.mods.customCS = args[0].get('customCS', 0)
                    player.mods.customHP = args[0].get('customHP', 0)
                except:
                    pass
                
                await sio.emit('playerModsChanged', (str(player.uid), args[0]), namespace=self.namespace)
                break
        
    async def on_roomModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.mods.mods = args[0]['mods']
        room_info.mods.speedMultiplier = args[0]['speedMultiplier']
        room_info.mods.flFollowDelay = args[0]['flFollowDelay']
        try:
            room_info.mods.customAR = args[0].get('customAR', 0)
            room_info.mods.customOD = args[0].get('customOD', 0)
            room_info.mods.customCS = args[0].get('customCS', 0)
            room_info.mods.customHP = args[0].get('customHP', 0)
        except:
            pass
        await sio.emit('roomModsChanged', args[0], namespace=self.namespace)
    
    async def on_roomSettingsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.gameplaySettings.isRemoveSliderLock = args[0].get('isRemoveSliderLock')
        room_info.gameplaySettings.isFreeMod = args[0].get('isFreeMod')
        room_info.gameplaySettings.allowForceDifficultyStatistics = args[0].get('allowForceDifficultyStatistics')
        await sio.emit('roomSettingsChanged', args[0], namespace=self.namespace)
    
    
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
    room.host = PlayerMulti().player(int(data['host']['uid']), sid='')
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
    room = []
    for room_id, room_info in glob.rooms.items():
        players = ''
        for p in room_info.players:
            players += p.as_json()['username']
        room.append({
            'id': room_info.id,
            'name': room_info.name,
            'isLocked': room_info.isLocked,
            'gameplaySettings': room_info.gameplaySettings.as_json(),
            'maxPlayers': room_info.maxPlayers,
            'mods': room_info.mods.as_json(),
            'playerNames': players,
            'playerCount': len(room_info.players),
            'status': room_info.status,
            'teamMode': room_info.teamMode,
            'winCondition': room_info.winCondition
        })
        
    return jsonify(room)
