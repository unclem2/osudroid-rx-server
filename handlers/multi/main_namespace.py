from handlers.multi import sio
import socketio
from objects import glob
from objects.room.utils import write_event
from handlers.multi.events.connection import ConnectionEvents
from handlers.multi.events.player import PlayerEvents
from handlers.multi.events.room import RoomEvents
from handlers.multi.events.match import MatchEvents
from handlers.multi.events.chat import ChatEvents
from handlers.multi.events.beatmap import BeatmapEvents
from handlers.multi.events.spectator import SpectatorEvents


class MultiNamespace(
    ConnectionEvents,
    PlayerEvents,
    RoomEvents,
    MatchEvents,
    ChatEvents,
    BeatmapEvents,
    SpectatorEvents,
    socketio.AsyncNamespace,
):
    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def room_id(self):
        return self.namespace.split("/")[-1]
    
    @property
    def room(self):
        return glob.rooms.get(id=self.room_id)

    async def trigger_event(self, event, sid, data=None, *args, **kwargs):
        handler_name = f"on_{event}"
        # if handler_name == "on_connect":
        #     self.receive_event(sid, event, args[0])
        # else:
        #     self.receive_event(sid, event, data)
        # if isinstance(data, bytes):
        #     super().trigger_event("binarydata", sid, data, *args, **kwargs)
        return await super().trigger_event(event, sid, data, *args, **kwargs)

    async def emit_event(
        self, event, data=None, namespace=None, to=None, skip_sid=None, *args, **kwargs
    ):
        if to:
            await sio.emit(event, data, namespace=namespace, to=to, *args, **kwargs)
        elif skip_sid:
            await sio.emit(event, data, namespace=namespace, skip_sid=skip_sid, *args, **kwargs)
        else:
            await sio.emit(event, data, namespace=namespace, *args, **kwargs)
        write_event(self.room_id, event, 0, data, receiver=to)

    def receive_event(self, sid, event, data=None):
        write_event(self.room_id, event, 1, data, sender=sid)
