from objects.room import PlayerStatus, RoomStatus, Match, WinCondition
from objects import glob


class MatchEvents:
    async def on_playBeatmap(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
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
            room_info.match.players.append(player)

    async def on_beatmapLoadComplete(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.beatmap_load_status[player.uid] = {"loaded": True}
        if len(room_info.match.beatmap_load_status) == len(room_info.match.players):
            await self.emit_event(
                "allPlayersBeatmapLoadComplete", namespace=self.namespace
            )

    async def on_skipRequested(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)

        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.skip_requests[player.uid] = {"skipped": True}

        if len(room_info.match.skip_requests) == len(room_info.match.players):
            await self.emit_event("allPlayersSkipRequested", namespace=self.namespace)

    async def on_liveScoreData(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        live_score_data = []

        for player in room_info.players:
            if player.sid == sid:
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

            if room_info.winCondition == WinCondition.SCOREV1:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["score"], reverse=True
                )
            elif room_info.winCondition == WinCondition.ACC:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["accuracy"], reverse=True
                )
            elif room_info.winCondition == WinCondition.COMBO:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["combo"], reverse=True
                )
            elif room_info.winCondition == WinCondition.SCOREV2:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["score"], reverse=True
                )

        await self.emit_event(
            "liveScoreData", live_score_data, namespace=self.namespace
        )

    async def on_scoreSubmission(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.submitted_scores[player.uid] = args[0]

        if len(room_info.match.submitted_scores) == len(room_info.match.players):
            data = []
            for player in room_info.match.players:
                try:
                    data.append(room_info.match.submitted_scores[player.uid])
                except:
                    pass

            if room_info.winCondition == WinCondition.SCOREV1:
                data = sorted(data, key=lambda x: x["score"], reverse=True)
            elif room_info.winCondition == WinCondition.ACC:
                data = sorted(data, key=lambda x: x["accuracy"], reverse=True)
            elif room_info.winCondition == WinCondition.COMBO:
                data = sorted(data, key=lambda x: x["combo"], reverse=True)
            elif room_info.winCondition == WinCondition.SCOREV2:
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
                    "playerStatusChanged", (str(player.uid), int(player.status))
                )

            room_info.match = Match()
