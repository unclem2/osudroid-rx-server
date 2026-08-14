from datetime import datetime

from pydantic import BaseModel, ConfigDict

from objects.enums.ranked_status import RankedStatus

from .beatmap_attrs import ProcessorBeatmapAttributesModel
from .beatmap_diff_attrs import ProcessorBeatmapDifficultyAttributesModel


class ProcessorBeatmapModel(BaseModel):
    id: int = 0
    set_id: int = 0
    md5: str = ""
    artist: str = ""
    title: str = ""
    version: str = ""
    creator: str = ""
    last_update: datetime = datetime.now()
    total_length: int = 0
    max_combo: int = 0
    bpm: float = 0.0
    attributes: ProcessorBeatmapAttributesModel | None = ProcessorBeatmapAttributesModel()
    star: ProcessorBeatmapDifficultyAttributesModel | None = ProcessorBeatmapDifficultyAttributesModel()
    status: RankedStatus | None = RankedStatus.Pending

    model_config = ConfigDict(from_attributes=True)
