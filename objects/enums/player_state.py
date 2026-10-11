from enum import IntEnum


class PlayerState(IntEnum):
    PLAYING = 1
    PAUSED = 2
    IDLE = 3
    OFFLINE = 4