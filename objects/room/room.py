from objects.beatmap import Beatmap
from .player import PlayerMulti
from .settings import RoomSettings
from .match import Match
from .consts import RoomStatus, WinCondition
from typing import Optional, Union
import osudroid_api_wrapper as od


class Room:
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.map: Beatmap = None
        self.host: PlayerMulti = PlayerMulti()
        self.is_locked: bool = False
        self.gameplay_settings: RoomSettings = RoomSettings()
        self.max_players: int = 0
        self.mods: od.ModList = od.ModList()
        self.players: list[PlayerMulti] = []
        self.watchers: list[PlayerMulti] = []
        self.status: RoomStatus = RoomStatus.IDLE
        self.team_mode: int = 0
        self.win_condition: WinCondition = WinCondition.SCOREV1
        self.password: str = ""
        self.match = Match()

    def get_player(
        self, uid: Optional[int] = None, sid: Optional[str] = None
    ) -> Optional[PlayerMulti]:
        if uid is not None:
            for player in self.players:
                if player.uid == uid:
                    return player
        elif sid is not None:
            for player in self.players:
                if player.sid == sid:
                    return player
        return None

    @property
    def as_json(self) -> dict[str, Union[str, int, bool]]:
        return {
            "id": self.id,
            "name": self.name,
            "map": self.map.as_json if self.map else None,
            "host": self.host.as_json,
            "isLocked": self.is_locked,
            "gameplaySettings": self.gameplay_settings.as_json,
            "maxPlayers": self.max_players,
            "mods": self.mods.as_calculable_mods,
            "players": [player.as_json for player in self.players],
            "status": self.status,
            "teamMode": self.team_mode,
            "winCondition": self.win_condition,
            "match": self.match.as_json,
        }
