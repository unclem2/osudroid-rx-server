from objects import glob
from objects.room import PlayerMulti, PlayerStatus, RoomStatus, Match


class PlayerEvents:

    async def on_playerModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                mods = player.mods
                mods_data = args[0]
                mods.mods = mods_data["mods"]
                mods.speedMultiplier = mods_data["speedMultiplier"]
                mods.flFollowDelay = mods_data["flFollowDelay"]
                mods.customAR = mods_data.get("customAR", 0)
                mods.customOD = mods_data.get("customOD", 0)
                mods.customCS = mods_data.get("customCS", 0)
                mods.customHP = mods_data.get("customHP", 0)

                await self.emit_event(
                    "playerModsChanged",
                    (str(player.uid), mods_data),
                    namespace=self.namespace,
                )
                break

    async def on_playerStatusChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                if args[0] == 0:
                    player.status = PlayerStatus.IDLE
                    if (
                        room_info.status == RoomStatus.PLAYING
                        and player.status != PlayerStatus.IDLE
                    ):
                        room_info.match.live_score_data[player.uid] = {
                            "score": 0,
                            "combo": 0,
                            "accuracy": 0,
                            "isAlive": False,
                        }
                        room_info.match.submitted_scores[player.uid] = {
                            "score": 0,
                            "combo": 0,
                            "accuracy": 0,
                            "isAlive": False,
                        }
                        print(room_info.match.players)
                        room_info.match.players.remove(player)
                        print(room_info.match.players)
                    if len(room_info.match.players) == 0:
                        room_info.status = RoomStatus.IDLE
                        await self.emit_event(
                            "roomStatusChanged",
                            int(room_info.status),
                            namespace=self.namespace,
                        )
                        room_info.match = Match()
                if args[0] == 1:
                    player.status = PlayerStatus.READY
                if args[0] == 2:
                    player.status = PlayerStatus.NOMAP
                if args[0] == 3:
                    player.status = PlayerStatus.PLAYING
                await self.emit_event(
                    "playerStatusChanged",
                    (str(player.uid), int(player.status)),
                    namespace=self.namespace,
                )
                break

    async def on_hostChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.host = PlayerMulti().player(int(args[0]), sid=sid)
        await self.emit_event(
            event="hostChanged", data=str(room_info.host.uid), namespace=self.namespace
        )
        
    async def on_playerKicked(self, sid, *args):
        await self.emit_event("playerKicked", data=str(args[0]), namespace=self.namespace)
