import logging
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import objects.schemas
from objects.schemas.base import Base

logger = logging.getLogger(__name__)

load_dotenv()

engine = create_async_engine(
    os.getenv("DATABASE_URL"),
    # echo=True
)

sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


async def init(engine) -> None:
    async with engine.connect() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        logger.debug("Registered models: %s", list(Base.registry._class_registry.keys()))
        await conn.run_sync(Base.metadata.create_all)
        stat_columns = (
            "h300", "hgeki", "h100", "hkatsu", "h50", "hmiss",
            "rank_xh", "rank_x", "rank_sh", "rank_s", "rank_a",
            "rank_b", "rank_c", "rank_d",
        )
        for column in stat_columns:
            await conn.execute(text(
                f'ALTER TABLE stats ADD COLUMN IF NOT EXISTS "{column}" integer NOT NULL DEFAULT 0'
            ))
        await conn.commit()
