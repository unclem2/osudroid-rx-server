from objects import glob


class ChatEvents:
    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        #TODO change this
        for a in room_info.players:
            await self.emit_event(
                "chatMessage",
                data=(str(player.uid), args[0]),
                namespace=self.namespace,
                to=a.sid
            )
        for watcher in room_info.watchers:
            await self.emit_event(
                "chatMessage",
                data=(player.username, args[0]),
                namespace=self.namespace,
                to=watcher.sid
            )
