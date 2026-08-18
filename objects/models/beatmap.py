from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer

from objects.enums.ranked_status import RankedStatus


class BeatmapModel(BaseModel):
    id: int = 0
    set_id: int = 0
    md5: str = ""
    artist: str = ""
    title: str = ""
    version: str = ""
    creator: str = ""
    last_update: datetime = Field(default_factory=datetime.now)
    total_length: int = 0
    max_combo: int = 0
    status: RankedStatus = RankedStatus.WIP
    bpm: float = 0.0
    cs: float = 0.0
    od: float = 0.0
    ar: float = 0.0
    hp: float = 0.0
    star: float = 0.0
    pp_version: str = ""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("last_update")
    def serialize_last_update(self, last_update: datetime) -> str:
        return last_update.isoformat()

    @computed_field
    @property
    def full(self) -> str:
        """Full name of the beatmap in the format: Artist - Title [Version]"""
        return f"{self.artist} - {self.title} [{self.version}]"

    @computed_field
    @property
    def gives_reward(self) -> bool:
        """True if the beatmap is ranked, approved, loved, or whitelisted"""
        return self.status in {
            1,   # Ranked
            2,   # Approved
            4,   # Loved
            5,    # Whitelisted
        }

    @property
    def filename(self) -> str:
        """Filename of the beatmap in the format: ID.osu"""
        return f"{self.id}.osu"

    @computed_field
    @property
    def map_link(self) -> str:
        return f"https://osu.ppy.sh/b/{self.id}"

    @computed_field
    @property
    def map_cover(self) -> str:
        return f"https://assets.ppy.sh/beatmaps/{self.set_id}/covers/cover.jpg"