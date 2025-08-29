import asyncio
from objects import glob
from osudroid_api_wrapper import ModList
from objects.room.consts import RoomStatus
from objects.room.match import Match
from objects.beatmap import Beatmap
import random

class ChatEvents:
    async def help(self):
        functions = dir(self)


    async def set_map(self, bid):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        beatmap = await Beatmap.from_bid(int(bid))
        if beatmap is None:
            return
        room_info.map = beatmap

        return_data = {}
        return_data["md5"] = room_info.map.md5
        return_data["title"] = room_info.map.title
        return_data["artist"] = room_info.map.artist
        return_data["version"] = room_info.map.version
        return_data["creator"] = room_info.map.creator
        if hasattr(room_info.map, "set_id"):
            return_data["beatmapSetId"] = room_info.map.set_id

        await self.emit_event("beatmapChanged", data=return_data)

    async def set_mods(self, mods):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        mods_data = mods
        #TODO make from_string
        # room_info.mods = ModList.from_string(mods)

        # await self.emit_event("roomModsChanged", room_info.mods.as_droid_mods)
        # await self.emit_event("chatMessage", data=(None, f"Mods set to {room_info.mods.as_standard_mods}"))

    async def kick(self, uid):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        kick_player = room_info.get_player(uid=int(uid))
        if kick_player is None:
            return
        await self.emit_event("playerKicked", data=str(kick_player.uid))

    async def abort(self):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        room_info.status = RoomStatus.IDLE
        room_info.match = Match()
        await self.emit_event("abortBeatmap")
        await self.emit_event("roomStatusChanged", data=room_info.status)

    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        await self.emit_event(
            "chatMessage",
            data=(str(player.uid), args[0]), skip_sid=[watcher.sid for watcher in room_info.watchers]
        )
        await self.emit_event(
            "chatMessage",
            data=(str(player.username), args[0]), skip_sid=[player.sid for player in room_info.players]
        )
        command = args[0].split(" ")[0]
        if not command.startswith("!"):
            return
        command_args = args[0].split(" ")[1:]
        match command:
            case "!help":
                await self.help()
            case "!setmap":
                if player.uid != room_info.host.uid:
                    return
                if len(command_args) == 0:
                    return
                await self.set_map(command_args[0])
            case "!setmods":
                if player.uid != room_info.host.uid:
                    return
                if len(command_args) == 0:
                    return
                await self.set_mods(command_args[0])
            case "!kick":
                if player.uid != room_info.host.uid:
                    return
                if len(command_args) == 0:
                    return
                await self.kick(command_args[0])
            case "!debug":
                if int(player.uid) != 2:
                    return
                self.debug = not self.debug
                await self.emit_event("chatMessage", data=(None, f"{'on' if self.debug else 'off'}"), to=sid)
            case "!dd":
                await self.emit_event("chatMessage", data=(None, str(room_info.as_json)), to=sid)
            case "!abort":
                if player.uid != room_info.host.uid:
                    return
                if room_info.status != RoomStatus.PLAYING:
                    return
                await self.abort()
            case "!start":
                if player.uid != room_info.host.uid:
                    return
                if room_info.status != RoomStatus.IDLE:
                    return
                for i in range(int(command_args[0])):
                    await asyncio.sleep(1)
                    await self.emit_event("chatMessage", data=(None, f"{int(command_args[0])-i}"))
                await self.on_playBeatmap(sid)
            case "!roll":
                roll = random.randint(1, 100)
                await self.emit_event("chatMessage", data=(None, f"{player.username} rolled {roll}"))