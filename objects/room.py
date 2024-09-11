from objects.player import Player
from objects.beatmap import Beatmap
from objects import glob
from enum import IntEnum, unique
from typing import Dict


class RoomStatus(IntEnum):
    OPEN = 1
    LOCKED = 2
    INGAME = 3

    def __repr__(self) -> str:
        return {
            self.OPEN: 'Open',
            self.LOCKED: 'Locked',
            self.INGAME: 'Ingame'
        }[self.value]
        


class Room:
    def __init__(self):
        self.id: int = 0
        self.name: str = ''
        self.isLocked: bool = False
        self.gameplaySettings: Dict[str, bool] = {
            'isRemoveSliderLock': False,
            'isFreeMod': False,
            'allowForceDifficultyStatistics': False,
        }
        self.maxPlayers: int = 0
        # self.mods: int = 0
        self.host: Player = None
        self.players: list = []
        
        self.map: Beatmap = None
        self.teamMode: int = 0
        self.winCondition: int = 0
        # self.status: RoomStatus = RoomStatus.OPEN
        self.password: str = ''
        
