from typing import Any, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel

from .beatmap import BeatmapModel
from .player import PlayerModel
from .score import ScoreModel


T = TypeVar("T")


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any


class ErrorResponse(BaseModel):
    status: str
    data: str


class PlayerSuccessResponse(BaseModel):
    status: str = "success"
    data: PlayerModel


class PlayerListSuccessResponse(BaseModel):
    status: str = "success"
    data: List[PlayerModel]


class BeatmapSuccessResponse(BaseModel):
    status: str = "success"
    data: BeatmapModel


class BeatmapListSuccessResponse(BaseModel):
    status: str = "success"
    data: List[BeatmapModel]


class ScoreSuccessResponse(BaseModel):
    status: str = "success"
    data: ScoreModel


class ScoreListSuccessResponse(BaseModel):
    status: str = "success"
    data: List[ScoreModel]


class OnlineCountResponse(BaseModel):
    status: str = "success"
    data: int


class CountryListResponse(BaseModel):
    status: str = "success"
    data: List[str]


class WhitelistResponse(BaseModel):
    status: str = "success"
    data: List[dict]
