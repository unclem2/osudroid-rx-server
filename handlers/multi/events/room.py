from objects import glob
from objects.room import PlayerMulti, PlayerStatus, Room, WinCondition, PlayerTeam
from osudroid_api_wrapper import ModList

class RoomEvents:
    async def on_roomModsChanged(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
        mods_data = args[0]
        room_info.mods = ModList.from_dict(mods_data)

        await self.emit_event("roomModsChanged", room_info.mods.as_json, namespace=self.namespace)

    async def on_roomGameplaySettingsChanged(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
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
            namespace=self.namespace,
        )

    async def on_roomNameChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        room_info.name = args[0]
        await self.emit_event(
            "roomNameChanged", data=str(room_info.name), namespace=self.namespace
        )

    async def on_roomPasswordChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        new_password = args[0]

        if new_password == "":
            room_info.is_locked = False
            room_info.password = ""
        else:
            room_info.is_locked = True
            room_info.password = new_password

    async def on_winConditionChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        if args[0] == 0:
            room_info.win_condition = WinCondition.SCOREV1
        if args[0] == 1:
            room_info.win_condition = WinCondition.ACC
        if args[0] == 2:
            room_info.win_condition = WinCondition.COMBO
        if args[0] == 3:
            room_info.win_condition = WinCondition.SCOREV2

        await self.emit_event(
            "winConditionChanged", data=room_info.win_condition, namespace=self.namespace
        )

    async def on_teamModeChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        room_info.team_mode = args[0]
        await self.emit_event(
            "teamModeChanged", room_info.team_mode, namespace=self.namespace
        )
        for player in room_info.players:
            player.team = None
            await self.emit_event(
                "playerStatusChanged",
                (str(player.uid), int(PlayerStatus.IDLE)),
                namespace=self.namespace,
            )
            await self.emit_event(
                "teamChanged",
                data=(str(player.uid), player.team),
                namespace=self.namespace,
            )

    async def on_teamChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        player: PlayerMulti = room_info.get_player(sid=sid)
        if player is None:
            return
        

        if args[0] == 0:
            player.team = PlayerTeam.RED
        if args[0] == 1:
            player.team = PlayerTeam.BLUE
        await self.emit_event(
            "teamChanged",
            data=(str(player.uid), player.team),
            namespace=self.namespace,
        )

    async def on_maxPlayersChanged(self, sid, *args):
        room_info = glob.rooms.get(id=self.room_id)
        room_info.max_players = args[0]
        await self.emit_event(
            "maxPlayersChanged",
            data=str(room_info.max_players),
            namespace=self.namespace,
        )
