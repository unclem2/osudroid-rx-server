from pydantic import BaseModel


class ProcessorCalculateRequestModel(BaseModel):
    beatmap_id: int | None = None
    md5: str | None = None
    acc: float | None = 100
    miss: int | None = 0
    combo: int | None = None
    h300: int | None = None
    h100: int | None = None
    h50: int | None = None
    hgeki: int | None = None
    hkatsu: int | None = None
    slidertickhits: int | None = None
    sliderendhits: int | None = None
    mods: list[dict] = []

