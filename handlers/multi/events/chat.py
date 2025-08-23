from objects import glob


class ChatEvents:
    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        await self.emit_event(
            "chatMessage",
            data=(str(player.uid), args[0]),
             
        )
        match args[0]:
            case "!help":
                pass
            case "!name":
                pass
            case "!setmods":
                pass
            case "!kick":
                pass
            case "!debug":
                self.debug = not self.debug
                await self.emit_event("chatMessage", data=(None, f"{'on' if self.debug else 'off'}"), to=sid)