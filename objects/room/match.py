from .player import PlayerMulti


class Match:
    def __init__(self):
        self.beatmap_load_status: dict[int, bool] = {}
        self.skip_requests: dict[int, bool] = {}
        self.live_score_data: dict = {}
        self.submitted_scores: dict = {}
        self.players: list[PlayerMulti] = []

    def add_player(self, player: PlayerMulti) -> None:
        if player not in self.players:
            self.players.append(player)
            self.live_score_data[player.uid] = {
                "score": None,
                "combo": None,
                "accuracy": None,
                "isAlive": True,
            }
            self.submitted_scores[player.uid] = {
                "accuracy": None,
                "score": None,
                "username": player.username,
                "mods": [],
                "maxCombo": None,
                "geki": None,
                "perfect": None,
                "katu": None,
                "good": None,
                "bad": None,
                "miss": None,
                "isAlive": True,
            }
            self.beatmap_load_status[player.uid] = False
            self.skip_requests[player.uid] = False

    def remove_player(self, player: PlayerMulti) -> None:
        if player in self.players:
            self.players.remove(player)
            self.live_score_data.pop(player.uid, None)
            self.submitted_scores.pop(player.uid, None)
            self.beatmap_load_status.pop(player.uid, None)
            self.skip_requests.pop(player.uid, None)

    def skipped(self, uid) -> None:
        self.skip_requests[uid] = True

    def submitted(self, uid, score_data) -> None:
        self.submitted_scores[uid] = score_data

    def loaded(self, uid) -> None:
        self.beatmap_load_status[uid] = True

    @property
    def all_loaded(self) -> bool:
        return all(self.beatmap_load_status.values())

    @property
    def all_skipped(self) -> bool:
        return all(self.skip_requests.values())

    @property
    def all_submitted(self) -> bool:
        return all(score["score"] != None for score in self.submitted_scores.values())

    @property
    def as_json(self) -> dict[str, dict]:
        return {
            "beatmap_load_status": self.beatmap_load_status,
            "skip_requests": self.skip_requests,
            "live_score_data": self.live_score_data,
            "submitted_scores": self.submitted_scores,
            "players": [player.as_json for player in self.players],
        }
