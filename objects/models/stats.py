from pydantic import BaseModel, ConfigDict, Field


class StatsModel(BaseModel):
    id : int = 0
    playcount: int = 0
    ranked_score: int = 0
    total_score: int = 0
    pp: float = 0.0
    accuracy: float = 0.0
    h300: int = 0
    hgeki: int = 0
    h100: int = 0
    hkatsu: int = 0
    h50: int = 0
    hmiss: int = 0
    rank_xh: int = 0
    rank_x: int = 0
    rank_sh: int = 0
    rank_s: int = 0
    rank_a: int = 0
    rank_b: int = 0
    rank_c: int = 0
    rank_d: int = 0
    playcount_rank: int = Field(default=0, exclude=True)
    accuracy_rank: int = Field(default=0, exclude=True)
    h300_rank: int = Field(default=0, exclude=True)
    hgeki_rank: int = Field(default=0, exclude=True)
    h100_rank: int = Field(default=0, exclude=True)
    hkatsu_rank: int = Field(default=0, exclude=True)
    h50_rank: int = Field(default=0, exclude=True)
    hmiss_rank: int = Field(default=0, exclude=True)
    rank_xh_rank: int = Field(default=0, exclude=True)
    rank_x_rank: int = Field(default=0, exclude=True)
    rank_sh_rank: int = Field(default=0, exclude=True)
    rank_s_rank: int = Field(default=0, exclude=True)
    rank_a_rank: int = Field(default=0, exclude=True)
    rank_b_rank: int = Field(default=0, exclude=True)
    rank_c_rank: int = Field(default=0, exclude=True)
    rank_d_rank: int = Field(default=0, exclude=True)
    level: int = Field(default=0, exclude=True)  # Calculated

    def db_dump(self) -> dict:
        return self.model_dump(exclude={"level"})

    model_config = ConfigDict(from_attributes=True)
