from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, SmallInteger

from objects.enums.score_status import ScoreStatus
from objects.schemas.base import Base


class ScoreSchema(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    beatmap_id: Mapped[int] = mapped_column(ForeignKey("beatmaps.id"), nullable=False)
    md5: Mapped[str] = mapped_column(nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    score: Mapped[float] = mapped_column()
    max_combo: Mapped[int] = mapped_column()
    grade: Mapped[str] = mapped_column()
    slidertickhits: Mapped[int] = mapped_column()
    sliderendhits: Mapped[int] = mapped_column()
    sliderheadhits: Mapped[int] = mapped_column()
    sliderrepeathits: Mapped[int] = mapped_column()
    accuracy: Mapped[float] = mapped_column()
    h300: Mapped[int] = mapped_column()
    hgeki: Mapped[int] = mapped_column()
    h100: Mapped[int] = mapped_column()
    hkatsu: Mapped[int] = mapped_column()
    h50: Mapped[int] = mapped_column()
    hmiss: Mapped[int] = mapped_column()
    mods: Mapped[str] = mapped_column()
    pp: Mapped[float] = mapped_column()
    status: Mapped[ScoreStatus] = mapped_column(
        SmallInteger, nullable=False, index=True,
    )  # статус скора
    fc: Mapped[bool] = mapped_column()
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pp_version: Mapped[str] = mapped_column()

    beatmap = relationship("BeatmapSchema", lazy="joined")
    player = relationship("PlayerSchema", lazy="joined")
