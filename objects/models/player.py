from pydantic import BaseModel, ConfigDict, Field

from objects.enums.player_state import PlayerState
from objects.models.stats import StatsModel


class OnlineStateModel(BaseModel):
    player_state: PlayerState = PlayerState.OFFLINE
    playing: str | None = None
    last_online: float | None = None

class PlayerModel(BaseModel):
    id: int = Field(default=0)
    username: str = ""
    clan_id: int | None = None
    country: str = ""
    pp_rank: int = Field(default=0)  # Calculated
    pp_country_rank: int = Field(default=0)  # Calculated
    score_rank: int = Field(default=0)  # Calculated
    score_country_rank: int = Field(default=0)  # Calculated
    online_state: OnlineStateModel = OnlineStateModel()
    stats: StatsModel = StatsModel()

    def db_dump(self) -> dict:
        stats_dump = self.stats.db_dump()
        player_dump = self.model_dump(exclude={"pp_rank", "pp_country_rank", "score_rank", "score_country_rank", "online_state"})
        player_dump["stats"] = stats_dump
        return player_dump


    model_config = ConfigDict(from_attributes=True)

