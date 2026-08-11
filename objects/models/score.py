import json
from datetime import datetime

from osudroid_api_wrapper import ModList
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from objects.enums.submission_status import SubmissionStatus
from objects.models.beatmap import BeatmapModel
from objects.models.player import PlayerModel


class ScoreModel(BaseModel):
    id: int | None = None
    beatmap_id: int = 0
    md5: str = ""
    player_id: int = 0
    score: int = 0
    max_combo: int = 0
    grade: str = ""
    slidertickhits: int = -1
    sliderendhits: int = -1
    sliderheadhits: int = -1
    sliderrepeathits: int = -1
    accuracy: float = 0.0
    h300: int = 0
    hgeki: int = 0
    h100: int = 0
    hkatsu: int = 0
    h50: int = 0
    hmiss: int = 0
    mods: ModList = ModList()
    pp: float = 0.0
    fc: bool | None = None
    status: SubmissionStatus = SubmissionStatus.FAILED
    date: datetime = Field(default_factory=datetime.now)
    pp_version: str = ""

    @field_serializer("mods")
    def serialize_mods(self, mods: ModList) -> str:
        return mods.as_json_string

    @field_validator("mods", mode="before")
    def deserialize_mods(cls, mods: str | list[dict]) -> ModList:
        if isinstance(mods, str):
            mods = json.loads(mods)
        return ModList.from_dict(mods)

    beatmap: BeatmapModel = BeatmapModel()
    player: PlayerModel = PlayerModel()

    def db_dump(self):
        score = self.model_dump(exclude={"beatmap", "player"})
        return score

    @property
    def droid_string(self) -> str:
        """Returns the score in the format used by StatisticV2"""
        return (
            f"{self.mods.as_json_string} {self.score} {self.max_combo} {self.grade} "
            f"{self.hgeki} {self.h300} {self.hkatsu} {self.h100} "
            f"{self.h50} {self.hmiss} 1 {int(self.date.timestamp()) * 1000} "
            f"{self.sliderheadhits} {self.slidertickhits} {self.sliderrepeathits} {self.sliderendhits} "
            f"{self.accuracy} {self.fc} {self.player.username}"
        )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)
