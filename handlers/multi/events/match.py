from objects.room.enums import RoomStatus, PlayerStatus, WinCondition
from objects.room.match import Match
from objects.room.room import Room
from objects import glob


class MatchEvents:
    async def on_playBeatmap(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
        room_info.status = RoomStatus.PLAYING
        await self.emit_event(
            "roomStatusChanged", data=room_info.status, namespace=self.namespace
        )
        await self.emit_event("playBeatmap", namespace=self.namespace)
        for player in room_info.players:
            await self.emit_event(
                "playerStatusChanged",
                (str(player.uid), int(PlayerStatus.PLAYING)),
                namespace=self.namespace,
            )
            room_info.match.add_player(player)

    async def on_beatmapLoadComplete(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        room_info.match.loaded(player.uid)
        if room_info.match.all_loaded:
            await self.emit_event(
                "allPlayersBeatmapLoadComplete", namespace=self.namespace
            )
            watchers_data = {
                "mods": room_info.mods.as_calculatable_mods,
                "name": room_info.name,
                "playingPlayers": [player.as_json for player in room_info.players],
                "teamMode": room_info.team_mode,
            }
            for watcher in room_info.watchers:
                await self.emit_event(
                    "roundStarted",
                    data=watchers_data,
                    namespace=self.namespace,
                    to=watcher.sid,
                )

    async def on_skipRequested(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)

        player = room_info.get_player(sid=sid)
        if player is None:
            return
        room_info.match.skipped(player.uid)

        if room_info.match.all_skipped:
            await self.emit_event("allPlayersSkipRequested", namespace=self.namespace)
            await self.emit_event("skipPerformed", namespace=self.namespace)
            
    async def on_liveScoreData(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
        live_score_data = []

        for player in room_info.players:
            player = room_info.get_player(sid=sid)
            if player is None:
                continue

            room_info.match.live_score_data[player.uid] = args[0]

            if len(room_info.match.live_score_data) == len(room_info.match.players):
                live_score_data.append(
                    {
                        "username": player.username,
                        "score": room_info.match.live_score_data[player.uid]["score"],
                        "combo": room_info.match.live_score_data[player.uid]["combo"],
                        "accuracy": room_info.match.live_score_data[player.uid][
                            "accuracy"
                        ],
                        "isAlive": room_info.match.live_score_data[player.uid][
                            "isAlive"
                        ],
                    }
                )

            if (
                room_info.win_condition == WinCondition.SCOREV1
                or room_info.win_condition == WinCondition.SCOREV2
            ):
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["score"], reverse=True
                )
            elif room_info.win_condition == WinCondition.ACC:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["accuracy"], reverse=True
                )
            elif room_info.win_condition == WinCondition.COMBO:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["combo"], reverse=True
                )

        await self.emit_event(
            "liveScoreData", live_score_data, namespace=self.namespace
        )

    async def on_scoreSubmission(self, sid, *args):
        room_info: Room = glob.rooms.get(id=self.room_id)
        player = room_info.get_player(sid=sid)
        if player is None:
            return
        room_info.match.submitted(player.uid, args[0])

        if room_info.match.all_submitted:
            data = []
            for player in room_info.match.players:
                try:
                    data.append(room_info.match.submitted_scores[player.uid])
                except:
                    pass

            if room_info.win_condition == WinCondition.SCOREV1:
                data = sorted(data, key=lambda x: x["score"], reverse=True)
            elif room_info.win_condition == WinCondition.ACC:
                data = sorted(data, key=lambda x: x["accuracy"], reverse=True)
            elif room_info.win_condition == WinCondition.COMBO:
                data = sorted(data, key=lambda x: x["combo"], reverse=True)
            elif room_info.win_condition == WinCondition.SCOREV2:
                data = sorted(data, key=lambda x: x["score"], reverse=True)

            await self.emit_event(
                "allPlayersScoreSubmitted", data=data, namespace=self.namespace
            )

            room_info.status = RoomStatus.IDLE
            await self.emit_event(
                "roomStatusChanged", int(room_info.status), namespace=self.namespace
            )

            for player in room_info.players:
                player.status = PlayerStatus.IDLE
                await self.emit_event(
                    "playerStatusChanged", (str(player.uid), int(player.status)), namespace=self.namespace
                )

            for watcher in room_info.watchers:
                await self.emit_event(
                    "roundEnded",
                    namespace=self.namespace,
                    to=watcher.sid,
                )

            room_info.match = Match()
