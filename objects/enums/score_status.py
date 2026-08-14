from enum import IntEnum, unique


@unique
class ScoreStatus(IntEnum):
    DELISTED = -2
    UNRANKED = -1
    FAILED = 0
    SUBMITTED = 1
    BEST = 2
