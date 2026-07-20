from pydantic import BaseModel


class ProcessorBeatmapAttributesModel(BaseModel):
    ar: float = 0.0
    ar_hit_window: float = 0.0
    base_ar: float = 0.0
    base_od: float = 0.0
    clock_rate: float = 0.0
    cs: float = 0.0
    hp: float = 0.0
    od: float = 0.0
    od_great_hit_window: float = 0.0
    od_meh_hit_window: float = 0.0
    od_ok_hit_window: float = 0.0
