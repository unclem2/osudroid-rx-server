from objects import glob


class ChatEvents:
    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                await self.emit_event(
                    "chatMessage",
                    data=(str(player.uid), args[0]),
                    namespace=self.namespace,
                )
