from objects import glob
from objects.room.consts import WinCondition, PlayerStatus, PlayerTeam
from objects.room.player import PlayerMulti
from objects.room.room import Room
from osudroid_api_wrapper import ModList


class RoomEvents:
    async def on_roomModsChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        mods_data = args[0]
        room_info.mods = ModList.from_dict(mods_data)

        await self.emit_event("roomModsChanged", room_info.mods.as_droid_mods)

    async def on_roomGameplaySettingsChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        gameplay_settings = room_info.gameplay_settings
        settings_data = args[0]

        gameplay_settings.is_remove_sliderlock = settings_data.get(
            "isRemoveSliderLock", gameplay_settings.is_remove_sliderlock
        )
        gameplay_settings.is_freemod = settings_data.get(
            "isFreeMod", gameplay_settings.is_freemod
        )

        await self.emit_event(
            "roomGameplaySettingsChanged",
            gameplay_settings.as_json,
        )

    async def on_roomNameChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        room_info.name = args[0]
        await self.emit_event(
            "roomNameChanged",
            data=str(room_info.name),
        )

    async def on_roomPasswordChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        new_password = args[0]

        if new_password == "":
            room_info.is_locked = False
            room_info.password = ""
        else:
            room_info.is_locked = True
            room_info.password = new_password

    async def on_winConditionChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        if args[0]:
            room_info.win_condition = WinCondition(args[0])

        await self.emit_event(
            "winConditionChanged",
            data=room_info.win_condition,
        )

    async def on_teamModeChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        room_info.team_mode = args[0]
        await self.emit_event(
            "teamModeChanged",
            room_info.team_mode,
        )
        for player in room_info.players:
            player.team = None
            await self.emit_event(
                "playerStatusChanged",
                (str(player.uid), int(PlayerStatus.IDLE)),
            )
            await self.emit_event(
                "teamChanged",
                data=(str(player.uid), player.team),
            )

    async def on_teamChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        player = room_info.get_player(sid=sid)
        if player is None:
            return

        player.team = PlayerTeam(args[0])
        await self.emit_event(
            "teamChanged",
            data=(str(player.uid), player.team),
        )

    async def on_maxPlayersChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if room_info is None:
            return
        room_info.max_players = args[0]
        await self.emit_event(
            "maxPlayersChanged",
            data=str(room_info.max_players),
        )
