from objects import glob


class ChatEvents:
    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        await self.emit_event(
            "chatMessage",
            data=(str(player.uid), args[0]),
            namespace=self.namespace,
        )
