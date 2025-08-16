from pydantic import BaseModel
from .beatmap import BeatmapModel
from .player import PlayerModel


class ScoreModel(BaseModel):
    id: int = 0
    bmap: BeatmapModel | None = None
    md5: str = ""
    player: PlayerModel | None = None
    pp: float
    score: int = 0
    max_combo: int = 0
    mods: str = ""
    acc: float = 0
    h300: int = 0
    h100: int = 0
    h50: int = 0
    hmiss: int = 0
    hgeki: int = 0
    hkatsu: int = 0
    slidertickhits: int = 0
    sliderendhits: int = 0
    grade: str = ""
    local_placement: int = 0
    global_placement: int = 0
    fc: bool | None = None
    status: str = "SUBMITTED"
    date: int = 0
