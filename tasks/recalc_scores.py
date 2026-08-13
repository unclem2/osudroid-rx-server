import logging
import time
from collections.abc import Callable

from objects.clients.processor import ProcessorClient
from objects.db import sessionmaker
from objects.repositories.beatmap import BeatmapRepository
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService

logger = logging.getLogger(__name__)


async def recalc_beatmaps(beatmap_service: BeatmapService, current_version: str) -> int:
    session = sessionmaker()
    repository = BeatmapRepository(session, beatmap_service.repository.redis)
    outdated = await repository.get_outdated(current_version)
    if not outdated:
        logger.info("All beatmaps are up to date.")
        return 0

    logger.info("Found %d beatmaps with outdated pp_version.", len(outdated))
    recalculed = 0

    for i, beatmap in enumerate(outdated, 1):
        try:
            result = await beatmap_service.recalc_get(beatmap)
            if result:
                recalculed += 1
            if i % 50 == 0:
                logger.info("Beatmaps progress: %d/%d", i, len(outdated))
        except Exception:
            logger.exception("Failed to recalc beatmap %s", beatmap.md5)

    logger.info("Recalculated %d/%d beatmaps.", recalculed, len(outdated))
    return recalculed


async def recalc_scores(processor_client: ProcessorClient, score_repository: ScoreRepository, current_version: str) -> tuple[int, set[int]]:
    outdated = await score_repository.get_outdated(current_version)
    if not outdated:
        logger.info("All scores are up to date.")
        return 0, set()

    logger.info("Found %d scores with outdated pp_version.", len(outdated))
    affected_player_ids: set[int] = set()
    recalculed = 0

    for i, score in enumerate(outdated, 1):
        try:
            pp_attrs = await processor_client.calculate_score(score)
            if pp_attrs:
                new_pp = pp_attrs.total
                new_version = pp_attrs.pp_version
            else:
                new_pp = 0.0
                new_version = current_version

            await score_repository.update_pp(score.id, new_pp, new_version)
            affected_player_ids.add(score.player_id)
            recalculed += 1

            if i % 100 == 0:
                logger.info("Scores progress: %d/%d", i, len(outdated))
        except Exception:
            logger.exception("Failed to recalc score %d", score.id)

    logger.info("Recalculated %d/%d scores.", recalculed, len(outdated))
    return recalculed, affected_player_ids


async def update_affected_stats(player_service: PlayerService, player_ids: set[int]) -> int:
    if not player_ids:
        return 0

    logger.info("Updating stats for %d affected players...", len(player_ids))
    updated = 0

    for i, pid in enumerate(player_ids, 1):
        try:
            player = await player_service.from_uid(pid)
            if player:
                await player_service.update_stats(player)
                updated += 1
            if i % 50 == 0:
                logger.info("Stats progress: %d/%d", i, len(player_ids))
        except Exception:
            logger.exception("Failed to update stats for player %d", pid)

    logger.info("Updated stats for %d/%d players.", updated, len(player_ids))
    return updated


async def recalc(app_instance):
    start = time.perf_counter()
    logger.info("=== Score recalculation started ===")

    redis = app_instance.state.redis
    processor_client = ProcessorClient(app_instance.state.config)

    session = sessionmaker()
    player_repository = PlayerRepository(session, redis)
    score_repository = ScoreRepository(session, redis)
    lb_repository = LeaderboardRepository(session, redis)
    player_storage = PlayerStorage(session, redis)
    player_service = PlayerService(player_repository, lb_repository, player_storage, score_repository)

    beatmap_session = sessionmaker()
    beatmap_repository = BeatmapRepository(beatmap_session, redis)

    osu_api_client = app_instance.state.osu_api_client
    beatmap_service = BeatmapService(beatmap_repository, app_instance.state.config, processor_client, osu_api_client)

    current_version = await processor_client.get_pp_version()
    if not current_version:
        logger.error("Failed to get pp_version from processor. Aborting recalc.")
        return

    logger.info("Current pp_version: %s", current_version)

    await recalc_beatmaps(beatmap_service, current_version)
    score_count, affected_players = await recalc_scores(processor_client, score_repository, current_version)
    await update_affected_stats(player_service, affected_players)

    elapsed = time.perf_counter() - start
    logger.info("=== Recalculation finished in %.2fs ===", elapsed)


async def compose(app_instance) -> tuple[Callable, dict]:
    return recalc, app_instance
