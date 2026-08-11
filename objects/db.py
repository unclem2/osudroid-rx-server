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
)

sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


async def init(engine) -> None:
    async with engine.connect() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        logger.debug("Registered models: %s", list(Base.registry._class_registry.keys()))
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
