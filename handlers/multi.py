import socketio
from quart import Blueprint, request, jsonify
import json
from objects import glob
from objects.player import Player
from objects.room import Room, PlayerMulti, PlayerStatus, RoomStatus, WinCondition
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
        
        disconnected_player = None
        for player in room_info.players:
            if player.sid == sid:
                disconnected_player = player
                break
        
        await sio.emit('playerLeft', data=str(disconnected_player.uid), namespace=self.namespace)
            
        # Check if the disconnected player was the host
        if room_info.host.uid == disconnected_player.uid:
            # Assign a new host
            for new_host in room_info.players:
                if new_host.uid != disconnected_player.uid:
                    room_info.host = new_host
                    await sio.emit(event='hostChanged', data=str(room_info.host.uid), namespace=self.namespace)
                    break
            
        # Remove the player from the room
        for i in range(len(room_info.players)):
            if room_info.players[i] == disconnected_player:
                room_info.players.pop(i)
                break

        if len(room_info.players) == 0:
            glob.rooms.pop(self.room_id)
        
    async def on_connect(self, sid, environ, *args):
        
        print(f"Client connected: {sid}")
        room_info = glob.rooms.get(self.room_id)
        if room_info.isLocked == True:
            if args[0]['password'] != room_info.password:
                await sio.emit('error', 'Wrong password', namespace=self.namespace, to=sid)
                await sio.disconnect(sid=sid, namespace=self.namespace)
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
        # Emit initial connection event
        await sio.emit(data=resp, namespace=self.namespace, event='initialConnection', to=sid)

        # If there is only one player in the room, return early
        if len(room_info.players) == 1:
            return
        
        # Find the new player who just joined
        new_player = None
        for player in room_info.players:
            if player.sid == sid:
                new_player = player
                break

        # Notify other players about the new player joining
        for player in room_info.players:
            if player.sid != sid:
                await sio.emit('playerJoined', data=new_player.as_json(), namespace=self.namespace, to=player.sid)

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
      
    async def on_playerStatusChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                #what the point
                if args[0] == 0:
                    player.status = PlayerStatus.IDLE
                if args[0] == 1:
                    player.status = PlayerStatus.READY
                if args[0] == 2:
                    player.status = PlayerStatus.NOMAP
                if args[0] == 3:
                    player.status = PlayerStatus.PLAYING
                await sio.emit('playerStatusChanged', (str(player.uid), int(player.status)), namespace=self.namespace)
                break
      
    async def on_hostChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.host = PlayerMulti().player(int(args[0]), sid=sid)
        await sio.emit(event='hostChanged', data=str(room_info.host.uid), namespace=self.namespace)
                
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
     
    async def on_roomGameplaySettingsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.gameplaySettings.isRemoveSliderLock = args[0].get('isRemoveSliderLock', room_info.gameplaySettings.isRemoveSliderLock)
        room_info.gameplaySettings.isFreeMod = args[0].get('isFreeMod', room_info.gameplaySettings.isFreeMod)
        room_info.gameplaySettings.allowForceDifficultyStatistics = args[0].get('allowForceDifficultyStatistics', room_info.gameplaySettings.allowForceDifficultyStatistics)
        await sio.emit('roomGameplaySettingsChanged', room_info.gameplaySettings.as_json(), namespace=self.namespace)
    
    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                await sio.emit('chatMessage', data=(str(player.uid), args[0]), namespace=self.namespace)
  
    async def on_roomNameChanged(self, sid, *args):
        room_info = glob.room.get(self.room_id)
        room_info.name = args[0]
        await sio.emit('roomNameChanged', data=str(room_info.name))
    
    async def on_roomPasswordChanged(self, sid, *args):
        room_info = glob.room.get(self.room_id)
        if room_info.isLocked == True:
            room_info.password = args[0]
        if args[0] == "":
            room_info.isLocked = False
            room_info.password = ""
        if room_info.isLocked != True:
            room_info.isLocked = True
            room_info.password = args[0]
            
    async def on_winConditionChanged(self, sid, *args):
        room_info = glob.room.get(self.room_id)
        if args[0] == 0:
            room_info.winCondition = WinCondition.SCOREV1
        if args[0] == 1:
            room_info.winCondition = WinCondition.ACC
        if args[0] == 2:
            room_info.winCondition = WinCondition.COMBO
        if args[0] == 3:
            room_info.winCondition = WinCondition.SCOREV2
        await sio.emit('winConditionChanged', data=room_info.winCondition, namespace=self.namespace)
        
        
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
        room.isLocked = True
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
