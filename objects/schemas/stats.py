
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from objects.schemas.base import Base


class StatsSchema(Base):
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)
    pp: Mapped[float] = mapped_column()
    accuracy: Mapped[float] = mapped_column()
    playcount: Mapped[int] = mapped_column()
    total_score: Mapped[int] = mapped_column(BigInteger)
    ranked_score: Mapped[int] = mapped_column(BigInteger)
    h300: Mapped[int] = mapped_column(default=0)
    hgeki: Mapped[int] = mapped_column(default=0)
    h100: Mapped[int] = mapped_column(default=0)
    hkatsu: Mapped[int] = mapped_column(default=0)
    h50: Mapped[int] = mapped_column(default=0)
    hmiss: Mapped[int] = mapped_column(default=0)
    rank_xh: Mapped[int] = mapped_column(default=0)
    rank_x: Mapped[int] = mapped_column(default=0)
    rank_sh: Mapped[int] = mapped_column(default=0)
    rank_s: Mapped[int] = mapped_column(default=0)
    rank_a: Mapped[int] = mapped_column(default=0)
    rank_b: Mapped[int] = mapped_column(default=0)
    rank_c: Mapped[int] = mapped_column(default=0)
    rank_d: Mapped[int] = mapped_column(default=0)
    player = relationship("PlayerSchema", back_populates="stats", uselist=False)
