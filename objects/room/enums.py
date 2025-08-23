from enum import IntEnum


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


class WinCondition(IntEnum):
    SCOREV1 = 0
    ACC = 1
    COMBO = 2
    SCOREV2 = 3


class PlayerType(IntEnum):
    PLAYER = 0
    WATCHER = 1
    REFEREE = 2
