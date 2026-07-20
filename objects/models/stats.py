from pydantic import BaseModel, ConfigDict, Field


class StatsModel(BaseModel):
    id : int = 0
    playcount: int = 0
    ranked_score: int = 0
    total_score: int = 0
    pp: float = 0.0
    accuracy: float = 0.0
    level: int = Field(default=0, exclude=True)  # Calculated

    def db_dump(self) -> dict:
        return self.model_dump(exclude={"level"})

    model_config = ConfigDict(from_attributes=True)
