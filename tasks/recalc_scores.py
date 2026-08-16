import logging
import time
from collections.abc import Callable

from objects.clients.processor import ProcessorClient
from objects.services.recalc import RecalcService

logger = logging.getLogger(__name__)


async def recalc(app_instance):
    start = time.perf_counter()
    logger.info("=== Score recalculation started ===")

    redis = app_instance.state.redis
    processor_client = ProcessorClient(app_instance.state.config)
    config = app_instance.state.config
    osu_api_client = app_instance.state.osu_api_client

    service = RecalcService(processor_client, config, osu_api_client, redis)
    await service.recalc_all()

    elapsed = time.perf_counter() - start
    logger.info("=== Recalculation finished in %.2fs ===", elapsed)


async def compose(app_instance) -> tuple[Callable, dict]:
    return recalc, app_instance
