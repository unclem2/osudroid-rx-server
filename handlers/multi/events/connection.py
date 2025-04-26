from handlers.multi import sio
from objects import glob
from objects.room import PlayerMulti, Room
import utils


class ConnectionEvents:
    async def on_disconnect(self, sid, *args):
        print(f"Client disconnected: {sid}")
        room_info = glob.rooms.get(self.room_id)

        disconnected_player = None
        for player in room_info.players:
            if player.sid == sid:
                disconnected_player = player
                break

        await self.emit_event(
            "playerLeft", data=str(disconnected_player.uid), namespace=self.namespace
        )


        # Check if the disconnected player was the host
        if room_info.host.uid == disconnected_player.uid:
            # Assign a new host
            for new_host in room_info.players:
                if new_host.uid != disconnected_player.uid:
                    room_info.host = new_host
                    await self.emit_event(
                        event="hostChanged",
                        data=str(room_info.host.uid),
                        namespace=self.namespace,
                    )
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
        room_info:Room = glob.rooms.get(self.room_id)
        if room_info.isLocked == True:
            if args[0]["password"] != room_info.password:
                await self.emit_event(
                    "error", "Wrong password", namespace=self.namespace, to=sid
                )

                await sio.disconnect(sid=sid, namespace=self.namespace)
                return
        if len(room_info.players) >= room_info.maxPlayers:
            await self.emit_event(
                "error", "Room is full", namespace=self.namespace, to=sid
            )
            await sio.disconnect(sid=sid, namespace=self.namespace)
            return
        room_info.players.append(PlayerMulti().player(id=args[0]["uid"], sid=sid))

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
            "host": room_info.host.as_json(),
            "isLocked": room_info.isLocked,
            "gameplaySettings": room_info.gameplaySettings.as_json(),
            "maxPlayers": room_info.maxPlayers,
            "mods": room_info.mods.as_json(),
            "players": [p.as_json() for p in room_info.players],
            "status": room_info.status,
            "teamMode": room_info.teamMode,
            "winCondition": room_info.winCondition,
            "sessionId": utils.make_uuid(),
        }
        # Emit initial connection event
        await self.emit_event(
            data=resp, namespace=self.namespace, event="initialConnection", to=sid
        )


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
                await self.emit_event(
                    "playerJoined",
                    data=new_player.as_json(),
                    namespace=self.namespace,
                    to=player.sid,
                )
