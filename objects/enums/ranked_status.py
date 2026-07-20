from enum import IntEnum, unique


@unique
class RankedStatus(IntEnum):
    """Enum representing the ranked status of a beatmap.

    Attributes:
        Blacklisted (int): -3 — The beatmap is blacklisted (locally)
        Graveyard (int): -2 — The beatmap is in the graveyard (locally or on Bancho).
        WIP (int): -1 — The beatmap is WIP (Bancho).
        Pending (int): 0 — The beatmap is pending (Bancho).
        Ranked (int): 1 — The beatmap is ranked (Bancho).
        Approved (int): 2 — The beatmap is approved (Bancho).
        Qualified (int): 3 — The beatmap is qualified (Bancho).
        Loved (int): 4 — The beatmap is loved (Bancho).
        Whitelisted (int): 5 — The beatmap is whitelisted (locally).

    """

    Blacklisted = -3
    Graveyard = -2
    WIP = -1
    Pending = 0
    Ranked = 1
    Approved = 2
    Qualified = 3
    Loved = 4
    Whitelisted = 5
