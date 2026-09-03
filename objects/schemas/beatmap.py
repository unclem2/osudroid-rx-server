from datetime import datetime

from sqlalchemy import SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from objects.enums.ranked_status import RankedStatus
from objects.schemas.base import Base


class BeatmapSchema(Base):
    __tablename__ = "beatmaps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    set_id: Mapped[int] = mapped_column(nullable=False)
    md5: Mapped[str] = mapped_column(nullable=False, index=True)
    artist: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    version: Mapped[str] = mapped_column(nullable=False)
    creator: Mapped[str] = mapped_column(nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    total_length: Mapped[int] = mapped_column()
    max_combo: Mapped[int] = mapped_column()
    bpm: Mapped[float] = mapped_column()

    status: Mapped[RankedStatus] = mapped_column(
        SmallInteger,
        nullable=False,
        index=True,
    )
    ar: Mapped[float] = mapped_column()
    cs: Mapped[float] = mapped_column()
    od: Mapped[float] = mapped_column()
    hp: Mapped[float] = mapped_column()
    star: Mapped[float] = mapped_column()
    pp_version: Mapped[str] = mapped_column(index=True)

    
