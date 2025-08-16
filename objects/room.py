from objects.beatmap import Beatmap
from objects import glob
from enum import IntEnum
from typing import Dict, Union
import json
import os
import time
import osudroid_api_wrapper as od
from typing import Optional


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

class WinCondition:
    SCOREV1 = 0
    ACC = 1
    COMBO = 2
    SCOREV2 = 3

class RoomSettings:
    def __init__(self):
        self.is_remove_sliderlock: bool = False
        self.is_freemod: bool = False

    @property
    def as_json(self) -> dict[str, bool]:
        return {
            "isRemoveSliderLock": self.is_remove_sliderlock,
            "isFreeMod": self.is_freemod,
        }



class PlayerMulti:
    def __init__(self):
        self.uid: int = 0
        self.username: str = ""
        self.status: PlayerStatus = PlayerStatus.IDLE
        self.team: int = 0
        self.mods: od.ModList = od.ModList()
        self.sid: str = ""

    @property
    def as_json(self) -> Dict[str, str]:
        return {
            "uid": self.uid,
            "username": self.username,
            "status": self.status,
            "team": self.team,
            "mods": self.mods.as_json,
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

        return instance



class Match:
    def __init__(self):
        self.beatmap_load_status: dict[int, bool] = {}
        self.skip_requests: dict[int, bool]
        self.live_score_data: dict = {}
        self.submitted_scores: dict = {}
        self.players: list[PlayerMulti] = []

    @property
    def as_json(self) -> dict[str, dict]:
        return {
            "beatmap_load_status": self.beatmap_load_status,
            "skip_requests": self.skip_requests,
            "live_score_data": self.live_score_data,
            "submitted_scores": self.submitted_scores,
            "players": [player.as_json for player in self.players],
        }


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
        self.status: RoomStatus = RoomStatus.IDLE
        self.team_mode: int = 0
        self.win_condition: WinCondition = WinCondition.SCOREV1
        self.password: str = ""
        self.match = Match()

    def get_player(self, uid: Optional[int] = None, sid: Optional[str] = None) -> Optional[PlayerMulti]:
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
            "mods": self.mods.as_json,
            "players": [player.as_json for player in self.players],
            "status": self.status,
            "teamMode": self.team_mode,
            "winCondition": self.win_condition,
            "match": self.match.as_json,
        }


def write_event(
    id: int, event: str, direction: int, data: dict, receiver=None, sender=None
):
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
        return "1"
    else:
        ids = [int(room.split(".")[0]) for room in rooms]
        return str(max(ids) + 1)
