from pydantic import BaseModel


class ProcessorBeatmapDifficultyAttributesModel(BaseModel):
    speed: float = 0.0
    aim: float = 0.0
    flashlight: float = 0.0
    total: float = 0.0

    pp_version: str = ""

i used models from pp processor in the server and can just parse json response