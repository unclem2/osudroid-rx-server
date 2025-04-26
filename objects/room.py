from objects.beatmap import Beatmap
from objects import glob
from enum import IntEnum
from typing import Dict, Union
import json
import os
import time


class RoomStatus(IntEnum):
    IDLE = 0
    CHANGING_BEATMAP = 1
    PLAYING = 2


class PlayerStatus(IntEnum):
    IDLE = 0
    READY = 1
    NOMAP = 2
    PLAYING = 3


class PlayerTeam(IntEnum):
    RED = 0
    BLUE = 1


class Mods:
    def __init__(self):
        self.mods: str = ""
        self.speedMultiplier: float = 1.0
        self.flFollowDelay: float = 0.12
        self.customAR: int = 0
        self.customOD: int = 0
        self.customCS: int = 0
        self.customHP: int = 0

    def as_json(self) -> Dict[str, Union[str, float, int]]:
        attributes = {
            "mods": self.mods,
            "speedMultiplier": self.speedMultiplier,
            "flFollowDelay": self.flFollowDelay,
            "customAR": self.customAR,
            "customOD": self.customOD,
            "customCS": self.customCS,
            "customHP": self.customHP,
        }
        filtered_attributes = {k: v for k, v in attributes.items() if v}
        return filtered_attributes


class PlayerMulti:
    def __init__(self):
        self.uid: int = 0
        self.username: str = ""
        self.status: PlayerStatus = PlayerStatus.IDLE
        self.team: int = 0
        self.mods: Mods = Mods()
        self.sid: str = ""

    def as_json(self) -> Dict[str, str]:
        return {
            "uid": self.uid,
            "username": self.username,
            "status": self.status,
            "team": self.team,
            "mods": self.mods.as_json(),
        }

    def player(self, id, sid):
        player = glob.players.get(id=int(id))
        self.uid = player.id
        self.username = player.name
        self.status = PlayerStatus.IDLE
        self.team = None
        self.mods = Mods()
        self.sid = sid

        return self


class RoomSettings:
    def __init__(self):
        self.isRemoveSliderLock: bool = False
        self.isFreeMod: bool = False
        self.allowForceDifficultyStatistics: bool = False

    def as_json(self) -> dict[str, bool]:
        return {
            "isRemoveSliderLock": self.isRemoveSliderLock,
            "isFreeMod": self.isFreeMod,
            "allowForceDifficultyStatistics": self.allowForceDifficultyStatistics,
        }


class WinCondition:
    SCOREV1 = 0
    ACC = 1
    COMBO = 2
    SCOREV2 = 3


class Match:
    def __init__(self):
        self.beatmap_load_status: dict = {}
        self.skip_requests: dict = {}
        self.live_score_data: dict = {}
        self.submitted_scores: dict = {}
        self.players: list = []
        
    def as_json(self) -> dict[str, dict]:
        return {
            "beatmap_load_status": self.beatmap_load_status,
            "skip_requests": self.skip_requests,
            "live_score_data": self.live_score_data,
            "submitted_scores": self.submitted_scores,
            "players": [player.as_json() for player in self.players],
        }


class Room:
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
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
        self.password: str = ""
        self.match = Match()
        
    def as_json(self) -> dict[str, Union[str, int, bool]]:
        return {
            "id": self.id,
            "name": self.name,
            "map": self.map.as_json() if self.map else None,
            "host": self.host.as_json(),
            "isLocked": self.isLocked,
            "gameplaySettings": self.gameplaySettings.as_json(),
            "maxPlayers": self.maxPlayers,
            "mods": self.mods.as_json(),
            "players": [player.as_json() for player in self.players],
            "status": self.status,
            "teamMode": self.teamMode,
            "winCondition": self.winCondition,
            "match": self.match.as_json(),  
        }

def write_event(id: int, event: str, direction: int, data: dict, receiver = None, sender = None):
    """
    Write an event to a JSON file for a specific room.

    Args:
        id (int): The ID of the room.
        event (str): The event name.
        direction (int): The direction of the event (0 for out, 1 for in).
        data (dict): The data associated with the event.
        to (str, optional): The recipient of the event. Defaults to None.   
    """
    
    with open(f"data/rooms/{id}.jsonl", "a") as f:
        dump_data = {
            "event": event,
            "data": data,
            "direction": "out" if direction == 0 else "in",
            "timestamp": int(time.time()),
            "to": receiver,
            "from": sender,
        }
        json.dump(dump_data, f, ensure_ascii=False)
        f.write("\n")

def read_room_log(id: int) -> list:
    with open(f"data/rooms/{id}.jsonl", "r") as f:
        room_data = []
        for line in f.readlines():
            room_data.append(json.loads(line))
            
    return room_data


def get_id() -> str:
    """
    Get the next available room ID.

    Returns:
        int: The next available room ID.
    """
    
    rooms = os.listdir("data/rooms")
    if len(rooms) == 0:
        return '1'
    else:
        ids = [int(room.split(".")[0]) for room in rooms]
        return str(max(ids) + 1)