from handlers.multi import sio
from objects import glob
from objects.room.consts import RoomStatus
from objects.room.room import Room
from objects.room.player import PlayerMulti
import utils
import asyncio


class ConnectionEvents:
    async def on_disconnect(self, sid, *args):
        #TODO че то придумать с ошибками изза реконнекта и вообще блять там пиздец какой то
        print(f"Client disconnected: {sid}")
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return

        disconnected_player = room_info.get_player(sid=sid)
        if disconnected_player is None:
            return

        await self.emit_event(
            "playerLeft", data=str(disconnected_player.uid),  
        )

        if room_info.host.uid == disconnected_player.uid:
            for new_host in room_info.players:
                if new_host.uid != disconnected_player.uid:
                    room_info.host = new_host
                    await self.emit_event(
                        event="hostChanged",
                        data=str(room_info.host.uid),
                         
                    )
                    break

        if disconnected_player in room_info.players:
            room_info.players.remove(disconnected_player)

        if room_info.match.players:
            if disconnected_player in room_info.match.players:
                room_info.match.remove_player(disconnected_player)

        if len(room_info.players) == 0:
            glob.rooms.remove(room_info)

    async def on_connect(self, sid, environ, *args):
        print(f"Client connected: {sid}")
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            await sio.disconnect(sid=sid, namespace=self.namespace)
            return
   
        match args[0]["type"]:
            case "0":
                if room_info.is_locked == True:
                    if args[0]["password"] != room_info.password:
                        await self.emit_event("error", "Wrong password", to=sid)
                        await sio.disconnect(sid=sid, namespace=self.namespace)
                        return
                if len(room_info.players) >= room_info.max_players:
                    await self.emit_event("error", "Room is full", to=sid)
                    await sio.disconnect(sid=sid, namespace=self.namespace)
                    return
                room_info.players.append(PlayerMulti.player(id=args[0]["uid"], sid=sid))
                resp = {
                            "id": room_info.id,
                            "name": room_info.name,
                            "beatmap": {
                                "md5": room_info.map.md5,
                                "title": room_info.map.title,
                                "artist": room_info.map.artist,
                                "version": room_info.map.version,
                                "creator": room_info.map.creator,
                                "beatmapSetId": room_info.map.set_id,
                            },
                            "host": room_info.host.as_json,
                            "isLocked": room_info.is_locked,
                            "gameplaySettings": room_info.gameplay_settings.as_json,
                            "maxPlayers": room_info.max_players,
                            "mods": room_info.mods.as_droid_mods,
                            "players": [p.as_json for p in room_info.players],
                            "status": room_info.status,
                            "teamMode": room_info.team_mode,
                            "winCondition": room_info.win_condition,
                            "sessionId": utils.make_uuid(),
                        }     
                        
            case "1":
                room_info.watchers.append(
                    PlayerMulti.watcher(sid=sid)
                )
                resp = {
                    "beatmap": {
                        "md5": room_info.map.md5,
                        "title": room_info.map.title,
                        "artist": room_info.map.artist,
                        "version": room_info.map.version,
                        "creator": room_info.map.creator,
                        "beatmapSetId": room_info.map.set_id,
                    },
                    "isPlaying": room_info.status == RoomStatus.PLAYING.value,
                    "mods": room_info.mods.as_calculable_mods,
                    "name": room_info.name,
                    "playingPlayers": [player.as_json for player in room_info.players],
                    "teamMode": room_info.team_mode,
                }


        await self.emit_event(data=resp, event="initialConnection", to=sid)

        new_player = room_info.get_player(sid=sid)
        if new_player is None:
            return

        await self.emit_event("playerJoined", data=new_player.as_json, skip_sid=sid)
