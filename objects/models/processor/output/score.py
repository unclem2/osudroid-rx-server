from pydantic import BaseModel

from .beatmap import ProcessorBeatmapModel
from .performance_attrs import ProcessorPerformanceAttributesModel


class ProcessorScoreModel(BaseModel):
    bmap: ProcessorBeatmapModel = ProcessorBeatmapModel()
    md5: str = ""
    pp_attributes: ProcessorPerformanceAttributesModel = ProcessorPerformanceAttributesModel()
    score: int = 0
    max_combo: int = 0
    mods: str = ""
    accuracy: float = 0
    h300: int = 0
    h100: int = 0
    h50: int = 0
    hmiss: int = 0
    hgeki: int = 0
    hkatsu: int = 0
    slidertickhits: int = 0
    sliderendhits: int = 0
    sliderheadhits: int = 0
    sliderrepeathits: int = 0