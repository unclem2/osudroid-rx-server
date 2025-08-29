from objects import glob
from objects.room.consts import RoomStatus
from objects.room.room import Room
from objects.beatmap import Beatmap


class BeatmapEvents:
    async def on_beatmapChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        if args[0] == {}:
            room_info.status = RoomStatus.CHANGING_BEATMAP
            await self.emit_event("roomStatusChanged", int(room_info.status))
            await self.emit_event("beatmapChanged", data=args[0])
        if args[0] != {}:
            room_info.status = RoomStatus.IDLE
            await self.emit_event("roomStatusChanged", int(room_info.status))

            beatmap = await Beatmap.from_md5(args[0]["md5"])
            if beatmap is not None:
                room_info.map = beatmap
                room_info.map.md5 = args[0]["md5"]
            else:
                room_info.map = Beatmap()
                room_info.map.title = args[0].get("title", "")
                room_info.map.artist = args[0].get("artist", "")
                room_info.map.version = args[0].get("version", "")
                room_info.map.creator = args[0].get("creator", "")
                room_info.map.md5 = args[0].get("md5", "")

            return_data = {}
            return_data["md5"] = room_info.map.md5
            return_data["title"] = room_info.map.title
            return_data["artist"] = room_info.map.artist
            return_data["version"] = room_info.map.version
            return_data["creator"] = room_info.map.creator
            if hasattr(room_info.map, "set_id"):
                return_data["beatmapSetId"] = room_info.map.set_id

            await self.emit_event(
                "beatmapChanged", data=return_data
            )
