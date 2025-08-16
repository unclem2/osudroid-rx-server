from handlers.multi import sio
from objects import glob
from objects.room import PlayerMulti, Room
import utils
import asyncio


class ConnectionEvents:
    async def on_disconnect(self, sid, *args):
        print(f"Client disconnected: {sid}")
        room_info: Room = glob.rooms.get(id=self.room_id)

        disconnected_player = room_info.get_player(sid=sid)
        if disconnected_player is None:
            return

        await self.emit_event(
            "playerLeft", data=str(disconnected_player.uid), namespace=self.namespace
        )

        if room_info.host.uid == disconnected_player.uid:
            for new_host in room_info.players:
                if new_host.uid != disconnected_player.uid:
                    room_info.host = new_host
                    await self.emit_event(
                        event="hostChanged",
                        data=str(room_info.host.uid),
                        namespace=self.namespace,
                    )
                    break

        if disconnected_player in room_info.players:
            room_info.players.remove(disconnected_player)

        if room_info.match.players:
            if disconnected_player in room_info.match.players:
                room_info.match.players.remove(disconnected_player)
                for score_data in room_info.match.live_score_data:
                    if score_data.username == disconnected_player.username:
                        room_info.match.live_score_data.remove(score_data)
                        break

        if len(room_info.players) == 0:
            room_info.name = "Closing"
            room_info.isLocked = True
            asyncio.sleep(5)
            glob.rooms.remove(room_info)

    async def on_connect(self, sid, environ, *args):
        print(f"Client connected: {sid}")
        room_info: Room = glob.rooms.get(id=self.room_id)
        if room_info.is_locked == True:
            if args[0]["password"] != room_info.password:
                await self.emit_event(
                    "error", "Wrong password", namespace=self.namespace, to=sid
                )

                await sio.disconnect(sid=sid, namespace=self.namespace)
                return
        if len(room_info.players) >= room_info.max_players:
            await self.emit_event(
                "error", "Room is full", namespace=self.namespace, to=sid
            )
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
            "mods": room_info.mods.as_json,
            "players": [p.as_json for p in room_info.players],
            "status": room_info.status,
            "teamMode": room_info.team_mode,
            "winCondition": room_info.win_condition,
            "sessionId": utils.make_uuid(),
        }
        await self.emit_event(
            data=resp, namespace=self.namespace, event="initialConnection", to=sid
        )

        if len(room_info.players) == 1:
            return

        new_player = room_info.get_player(sid=sid)
        if new_player is None:
            return

        for player in room_info.players:
            if player.sid != sid:
                await self.emit_event(
                    "playerJoined",
                    data=new_player.as_json,
                    namespace=self.namespace,
                    to=player.sid,
                )
