from objects import glob
from handlers.multi import sio


class SpectatorEvents:
    async def on_spectatorData(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        player = room_info.get_player(sid=sid)
        placeholder = {"_placeholder": True, "num": 0}
        if player is None:
            return
        for watcher in room_info.watchers:

            await self.emit_event(
                "spectatorData",
                data=(str(player.uid), placeholder),
                to=watcher.sid,
                namespace=self.namespace,
            )
            await sio.eio.send(
                watcher.sid,
                args[0],
            )
