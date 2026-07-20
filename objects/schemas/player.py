
from sqlalchemy.orm import Mapped, mapped_column, relationship

from objects.schemas.base import Base


class PlayerSchema(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(nullable=False, index=True)
    clan_id: Mapped[int] = mapped_column(index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    device_id: Mapped[str] = mapped_column()
    email_hash: Mapped[str] = mapped_column()
    status: Mapped[int] = mapped_column()
    country: Mapped[str] = mapped_column(index=True)
    stats = relationship("StatsSchema", back_populates="player", uselist=False, lazy="joined")
