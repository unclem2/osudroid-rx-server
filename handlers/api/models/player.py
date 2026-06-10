from pydantic import BaseModel
from typing import Optional


class StatsModel(BaseModel):
    id: int = 0
    pp_rank: int = 0
    score_rank: int = 0
    tscore: int = 0
    rscore: int = 0
    acc: float = 0.0
    plays: int = 0
    pp: float = 0.0
    country_pp_rank: int = 0
    country_score_rank: int = 0
    playing: str | None = None


class PlayerModel(BaseModel):
    id: int = 0
    country: Optional[str] = None
    prefix: Optional[str] = None
    username: str = ""
    online: Optional[bool] = None
    stats: StatsModel = StatsModel()
