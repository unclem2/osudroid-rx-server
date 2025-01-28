import objects.replay_data.hitresult as hitresult
from typing import Optional, List


class ReplayObjectData:
    def __init__(
        self,
        accuracy: Optional[float],
        tickset: Optional[List[bool]],
        result: hitresult.HitResult,
    ):
        self.accuracy: float = accuracy
        self.tickset: List[bool] = tickset
        self.result: hitresult.HitResult = result
