import json
from objects import glob
from objects.room.consts import PlayerStatus, RoomStatus
from objects.room.match import Match
from objects.room.room import Room
from objects.room.player import PlayerMulti
from osudroid_api_wrapper import ModList


class PlayerEvents:
    async def on_playerModsChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return

        player.mods = ModList.from_dict(args[0])
        await self.emit_event(
            "playerModsChanged",
            (str(player.uid), player.mods.as_droid_mods),
        )

    async def on_playerStatusChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        if args[0] == 0:
            player.status = PlayerStatus.IDLE
            if (
                room_info.status == RoomStatus.PLAYING
                and player.status != PlayerStatus.IDLE
            ):
                room_info.match.remove_player(player)
            if len(room_info.match.players) == 0:
                room_info.status = RoomStatus.IDLE
                await self.emit_event(
                    "roomStatusChanged",
                    int(room_info.status),
                )
                room_info.match = Match()
        elif args[0] == 1:
            player.status = PlayerStatus.READY
        elif args[0] == 2:
            player.status = PlayerStatus.NOMAP
        elif args[0] == 3:
            player.status = PlayerStatus.PLAYING
        await self.emit_event(
            "playerStatusChanged",
            (str(player.uid), int(player.status)),
        )

    async def on_hostChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(uid=int(args[0]))
        if player is None:
            return
        room_info.host = player
        await self.emit_event(
            event="hostChanged",
            data=str(room_info.host.uid),
        )

    async def on_playerKicked(self, sid, *args):
        await self.emit_event(
            "playerKicked",
            data=str(args[0]),
        )
