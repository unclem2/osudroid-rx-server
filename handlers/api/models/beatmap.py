from pydantic import BaseModel
from datetime import datetime


class BeatmapModel(BaseModel):
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
    status: int = 0
    mode: int = 0
    bpm: float = 0.0
    cs: float = 0.0
    od: float = 0.0
    ar: float = 0.0
    hp: float = 0.0
    star: float = 0.0
