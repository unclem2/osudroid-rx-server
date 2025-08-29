from .consts import PlayerStatus, PlayerType
from objects import glob
import osudroid_api_wrapper as od
from typing import Dict


class PlayerMulti:
    def __init__(self):
        self.uid: int = 0
        self.username: str = ""
        self.status: PlayerStatus = PlayerStatus.IDLE
        self.team: int = 0
        self.mods: od.ModList = od.ModList()
        self.sid: str = ""
        self.type = PlayerType.PLAYER

    @property
    def as_json(self) -> Dict[str, str]:
        return {
            "uid": self.uid,
            "username": self.username,
            "status": self.status,
            "team": self.team,
            "mods": self.mods.as_calculable_mods,
        }

    @classmethod
    def player(cls, id, sid):
        player = glob.players.get(id=int(id))
        instance = cls()
        instance.uid = player.id
        instance.username = player.username
        instance.status = PlayerStatus.IDLE
        instance.team = None
        instance.mods = od.ModList()
        instance.sid = sid
        instance.type = PlayerType.PLAYER

        return instance

    @classmethod
    def watcher(cls, sid):
        instance = cls()
        instance.uid = 0
        instance.username = "Watcher"
        instance.sid = sid
        instance.type = PlayerType.WATCHER
        
        return instance
