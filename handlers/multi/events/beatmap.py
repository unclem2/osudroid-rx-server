from objects import glob
from objects.room import RoomStatus
from objects.beatmap import Beatmap


class BeatmapEvents:
    async def on_beatmapChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        if args[0] == {}:
            room_info.status = RoomStatus.CHANGING_BEATMAP
            await self.emit_event("beatmapChanged", data=args[0], namespace=self.namespace)
        if args[0] != {}:
            room_info.status = RoomStatus.IDLE
            try:
                room_info.map = await Beatmap.from_md5(args[0]["md5"])
                room_info.map.md5 = args[0]["md5"]
            except:
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
            try:
                return_data["beatmapSetId"] = room_info.map.set_id
            except:
                pass

            await self.emit_event("beatmapChanged", data=return_data, namespace=self.namespace)

