
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
    player = relationship("PlayerSchema", back_populates="stats", uselist=False)
