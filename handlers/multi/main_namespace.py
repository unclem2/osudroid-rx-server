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
        self.debug = False
        super().__init__(namespace)

    @property
    def room_id(self):
        return self.namespace.split("/")[-1]

    @property
    def room(self):
        return glob.rooms.get(id=self.room_id)

    @property
    def debug_mode(self):
        return self.debug

    async def trigger_event(self, event, sid, data=None, *args, **kwargs):
        handler_name = f"on_{event}"
        # TODO как то отфильтровать все ивенты и добавить все те которые нужны спектатор клиенту
        # желательно еще это как то абстрагировать
        if handler_name == "on_connect":
            self.receive_event(sid, event, args[0])
        else:
            self.receive_event(sid, event, data)
        if self.debug_mode:
            await sio.emit(
                event="chatMessage",
                data=(None, f"[in]{event} - {data}"),
                namespace=self.namespace,
            )
        return await super().trigger_event(event, sid, data, *args, **kwargs)

    async def emit_event(
        self, event, data=None, to=None, skip_sid=None, *args, **kwargs
    ):
        if to:
            await sio.emit(
                event=event, data=data, namespace=self.namespace, to=to, *args, **kwargs
            )
        elif skip_sid:
            await sio.emit(
                event=event,
                data=data,
                namespace=self.namespace,
                skip_sid=skip_sid,
                *args,
                **kwargs,
            )
        else:
            await sio.emit(
                event=event, data=data, namespace=self.namespace, *args, **kwargs
            )

        write_event(id=self.room_id, event=event, direction=0, data=data, receiver=to)
        if self.debug_mode:
            await sio.emit(
                event="chatMessage",
                data=(None, f"[out]{event} - {data}"),
                namespace=self.namespace,
            )

    def receive_event(self, sid, event, data=None):
        write_event(id=self.room_id, event=event, direction=1, data=data, sender=sid)
