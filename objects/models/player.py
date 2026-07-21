from pydantic import BaseModel, ConfigDict, Field

from objects.models.stats import StatsModel


class PlayerModel(BaseModel):
    id: int | None = None
    username: str = ""
    clan_id: int | None = None
    country: str = ""
    pp_rank: int = Field(default=0)  # Calculated
    pp_country_rank: int = Field(default=0)  # Calculated
    score_rank: int = Field(default=0)  # Calculated
    score_country_rank: int = Field(default=0)  # Calculated
    playing: str | None = Field(default=None)  # Calculated
    stats: StatsModel = Field(default=StatsModel(), exclude=True)

    def db_dump(self) -> dict:
        stats_dump = self.stats.db_dump()
        player_dump = self.model_dump(exclude={"pp_rank", "pp_country_rank", "score_rank", "score_country_rank", "playing"})
        player_dump["stats"] = stats_dump
        return player_dump

    model_config = ConfigDict(from_attributes=True)

