from pydantic import BaseModel


class ProcessorPerformanceAttributesModel(BaseModel):
    speed: float = 0.0
    aim: float = 0.0
    acc: float = 0.0
    flashlight: float = 0.0
    reading: float = 0.0
    total: float = 0.0
    effective_miss_count: int = 0
    pp_version: str = ""