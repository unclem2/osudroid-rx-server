from objects.player import Player
from objects.beatmap import Beatmap
from objects import glob
from enum import IntEnum, unique
from typing import Dict, Union


class RoomStatus(IntEnum):
    IDLE = 0
    CHANGING_BEATMAP = 1
    PLAYING = 2

    def __repr__(self) -> str:
        return {
            self.IDLE: 'Idle',
            self.CHANGING_BEATMAP: 'Changing beatmap',
            self.PLAYING: 'Playing'
        }[self.value]
        
class PlayerStatus(IntEnum):  #finished
    IDLE = 0
    READY = 1
    NOMAP = 2
    PLAYING = 3
    
    def __repr__(self) -> str:
        return {
            self.IDLE: 'Idle',
            self.READY: 'Ready',
            self.NOMAP: 'NoMap',
            self.PLAYING: 'Playing'
        }[self.value]
           
class PlayerTeam(IntEnum):  
    NONE = 0
    BLUE = 1
    RED = 2
    
    def __repr__(self) -> str:
        return {
            self.NONE: 'None',
            self.BLUE: 'Blue',
            self.RED: 'Red'
        }[self.value]
  
class Mods:  
    def __init__(self):
        self.mods: str = ''
        self.speedMultiplier: float = 1.0
        self.flFollowDelay: float = 0.12
        self.customAR: int = 0
        self.customOD: int = 0
        self.customCS: int = 0
        self.customHP: int = 0
        
    def as_json(self) -> Dict[str, Union[str, float, int]]:
        attributes = {
            'mods': self.mods,
            'speedMultiplier': self.speedMultiplier,
            'flFollowDelay': self.flFollowDelay,
            'customAR': self.customAR,
            'customOD': self.customOD,
            'customCS': self.customCS,
            'customHP': self.customHP
        }
        filtered_attributes = {k: v for k, v in attributes.items() if v}
        return filtered_attributes

class PlayerMulti:  
    def __init__(self):
        self.uid: int = 0
        self.username: str = ''
        self.status: PlayerStatus = PlayerStatus.IDLE
        self.team: int = 0
        self.mods: Mods = Mods()
        self.sid: str = ''
    
    def as_json(self) -> Dict[str, str]:
        return {
            'uid': self.uid,
            'username': self.username,
            'status': self.status,
            'team': self.team,
            'mods': self.mods.as_json()
        }
    
    def player(self, id, sid):
        player = glob.players.get(id=int(id))
        self.uid = player.id
        self.username = player.name
        self.status = PlayerStatus.IDLE
        self.team = PlayerTeam.NONE
        self.mods = Mods()
        self.sid = sid
        
        return self
    
        
class RoomSettings:  
    def __init__(self):
        self.isRemoveSliderLock: bool = False
        self.isFreeMod: bool = False
        self.allowForceDifficultyStatistics: bool = False  
    
    def as_json(self) -> Dict[str, str]:
        return {
            'isRemoveSliderLock': self.isRemoveSliderLock,
            'isFreeMod': self.isFreeMod,
            'allowForceDifficultyStatistics': self.allowForceDifficultyStatistics
        }
    
class WinCondition:
    SCOREV1 = 0
    ACC = 1
    COMBO = 2
    SCOREV2 = 3
    
    def __repr__(self) -> str:
        return {
            self.SCOREV1: 'Score v1',
            self.ACC: 'Accuracy',
            self.COMBO: 'Combo',
            self.SCOREV2: 'Score v2'
        }[self.value]

class Room:
    def __init__(self):
        self.id: int = 0
        self.name: str = ''
        self.map: Beatmap = None
        self.host: PlayerMulti = PlayerMulti()
        self.isLocked: bool = False
        self.gameplaySettings: RoomSettings = RoomSettings()
        self.maxPlayers: int = 0
        self.mods: Mods = Mods()
        self.players: list = []
        self.status: RoomStatus = RoomStatus.IDLE
        self.teamMode: int = 0
        self.winCondition: WinCondition = WinCondition.SCOREV1
        self.password: str = ''
        
    
        
