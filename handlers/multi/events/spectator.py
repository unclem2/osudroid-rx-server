from objects import glob
from handlers.multi import sio


class SpectatorEvents:
    async def on_spectatorData(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        for watcher in room_info.watchers:

            await self.emit_event(
                "spectatorData",
                data=(player.uid, args[0]),
                to=watcher.sid,
                 
            )