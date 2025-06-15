from objects import glob
from objects.room import PlayerStatus, WinCondition, PlayerTeam


class RoomEvents:
    async def on_roomModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        mods_data = args[0]
        mods = room_info.mods

        mods.mods = mods_data["mods"]
        mods.speedMultiplier = mods_data["speedMultiplier"]
        mods.flFollowDelay = mods_data["flFollowDelay"]
        mods.customAR = mods_data.get("customAR", 0)
        mods.customOD = mods_data.get("customOD", 0)
        mods.customCS = mods_data.get("customCS", 0)
        mods.customHP = mods_data.get("customHP", 0)

        await self.emit_event("roomModsChanged", mods_data, namespace=self.namespace)

    async def on_roomGameplaySettingsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        gameplay_settings = room_info.gameplaySettings
        settings_data = args[0]

        gameplay_settings.isRemoveSliderLock = settings_data.get(
            "isRemoveSliderLock", gameplay_settings.isRemoveSliderLock
        )
        gameplay_settings.isFreeMod = settings_data.get(
            "isFreeMod", gameplay_settings.isFreeMod
        )
        gameplay_settings.allowForceDifficultyStatistics = settings_data.get(
            "allowForceDifficultyStatistics",
            gameplay_settings.allowForceDifficultyStatistics,
        )

        await self.emit_event(
            "roomGameplaySettingsChanged",
            gameplay_settings.as_json(),
            namespace=self.namespace,
        )

    async def on_roomNameChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.name = args[0]
        await self.emit_event(
            "roomNameChanged", data=str(room_info.name), namespace=self.namespace
        )

    async def on_roomPasswordChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        new_password = args[0]

        if new_password == "":
            room_info.isLocked = False
            room_info.password = ""
        else:
            room_info.isLocked = True
            room_info.password = new_password

    async def on_winConditionChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        if args[0] == 0:
            room_info.winCondition = WinCondition.SCOREV1
        if args[0] == 1:
            room_info.winCondition = WinCondition.ACC
        if args[0] == 2:
            room_info.winCondition = WinCondition.COMBO
        if args[0] == 3:
            room_info.winCondition = WinCondition.SCOREV2

        await self.emit_event(
            "winConditionChanged", data=room_info.winCondition, namespace=self.namespace
        )

    async def on_teamModeChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.teamMode = args[0]
        await self.emit_event(
            "teamModeChanged", room_info.teamMode, namespace=self.namespace
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
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
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
        room_info = glob.rooms.get(self.room_id)
        room_info.maxPlayers = args[0]
        await self.emit_event(
            "maxPlayersChanged",
            data=str(room_info.maxPlayers),
            namespace=self.namespace,
        )
