import asyncio
import logging
import time
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import noload

from objects.clients.processor import ProcessorClient
from objects.db import sessionmaker
from objects.enums.score_status import ScoreStatus
from objects.models.processor.output.performance_attrs import (
    ProcessorPerformanceAttributesModel,
)
from objects.models.score import ScoreModel
from objects.repositories.beatmap import BeatmapRepository
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository
from objects.schemas.score import ScoreSchema
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService
from objects.services.score import ScoreService

logger = logging.getLogger(__name__)

# Bound concurrency for http calls to the pp processor
_PROCESSOR_CONCURRENCY = 8
_pp_semaphore = asyncio.Semaphore(_PROCESSOR_CONCURRENCY)


# Only the score columns required by the processor service need a Pydantic model;
# building one from an ORM row avoids loading joined beatmap/player rows.
def _to_score_model(row: ScoreSchema) -> ScoreModel:
    return ScoreModel(
        id=row.id,
        beatmap_id=row.beatmap_id,
        md5=row.md5,
        player_id=row.player_id,
        score=row.score,
        max_combo=row.max_combo,
        grade=row.grade,
        slidertickhits=row.slidertickhits,
        sliderendhits=row.sliderendhits,
        sliderheadhits=row.sliderheadhits,
        sliderrepeathits=row.sliderrepeathits,
        accuracy=row.accuracy,
        h300=row.h300,
        hgeki=row.hgeki,
        h100=row.h100,
        hkatsu=row.hkatsu,
        h50=row.h50,
        hmiss=row.hmiss,
        mods=row.mods,
        pp=row.pp,
        fc=row.fc,
        status=row.status,
        date=row.date,
        pp_version=row.pp_version,
    )


async def _calculate_pp(score_service: ScoreService, processor_client: ProcessorClient, row: ScoreSchema) -> ProcessorPerformanceAttributesModel | None:
    async with _pp_semaphore:
        model = _to_score_model(row)
        if score_service.is_ranked(model):
            return await processor_client.calculate_score(model)
    return None


# Simple in-memory state tracker for external monitoring/logs
recalc_state: dict = {
    "phase": None,
    "current": None,
    "processed": 0,
    "total": 0,
}


def _log_state_if_needed(force: bool = False) -> None:
    """Log current recalc_state at INFO level periodically or when forced."""
    # Avoid flooding logs; only log when forced or at natural progress checkpoints
    if force:
        logger.info("Recalc state: %s", recalc_state)
        return
    # Otherwise only log when processed is a round number (helpful checkpoints)
    processed = recalc_state.get("processed", 0)
    total = recalc_state.get("total", 0)
    if total and (processed % max(1, total // 10) == 0):
        logger.info("Recalc checkpoint: %s", recalc_state)


async def recalc_beatmaps(beatmap_service: BeatmapService, current_version: str) -> int:
    session = sessionmaker()
    repository = BeatmapRepository(session, beatmap_service.repository.redis)
    outdated = await repository.get_outdated(current_version)
    if not outdated:
        logger.info("All beatmaps are up to date.")
        return 0
    total = len(outdated)
    logger.info("Found %d beatmaps with outdated pp_version.", total)
    recalculed = 0

    # update state
    recalc_state["phase"] = "beatmaps"
    recalc_state["processed"] = 0
    recalc_state["total"] = total

    # fetch all beatmaps from the processor in parallel, then persist sequentially
    async def _fetch(beatmap):
        async with _pp_semaphore:
            return await beatmap_service.processor_client.md5_get_beatmap(beatmap.md5)

    fetched = await asyncio.gather(*(_fetch(beatmap) for beatmap in outdated))

    for i, (beatmap, new_beatmap) in enumerate(zip(outdated, fetched), 1):
        recalc_state["current"] = getattr(beatmap, "md5", None)
        recalc_state["processed"] = i
        if new_beatmap:
            try:
                await repository.save(new_beatmap)
                recalculed += 1
            except Exception:
                logger.exception("Failed to save recalculated beatmap %s", beatmap.md5)
        if i % 50 == 0:
            logger.info("Beatmaps progress: %d/%d", i, total)
            _log_state_if_needed()

    logger.info("Recalculated %d/%d beatmaps.", recalculed, total)
    recalc_state["current"] = None
    _log_state_if_needed(force=True)
    return recalculed


async def recalc_scores(score_service: ScoreService, processor_client: ProcessorClient, score_repository: ScoreRepository, current_version: str) -> tuple[int, set[int]]:
    session = score_repository.session

    # one lightweight query: md5s of maps that have any outdated score
    scores_stmt = (
        select(ScoreSchema)
        .where(
            ScoreSchema.md5.in_(
                select(ScoreSchema.md5)
                .where(ScoreSchema.pp_version != current_version),
            ),
        )
        .options(
            noload(ScoreSchema.beatmap),
            noload(ScoreSchema.player),
        )
    )

    rows = (await session.execute(scores_stmt)).scalars().all()

    by_map: dict[str, list[ScoreSchema]] = {}
    for row in rows:
        by_map.setdefault(row.md5, []).append(row)

    total_maps = len(by_map)
    total_scores = len(rows)
    logger.info("Found %d scores across %d maps with outdated pp_version.", total_scores, total_maps)

    recalc_state["phase"] = "scores"
    recalc_state["processed"] = 0
    recalc_state["total"] = total_maps

    affected_player_ids: set[int] = set()
    recalculed_scores = 0

    for map_index, (md5, map_scores) in enumerate(by_map.items(), 1):
        recalc_state["current"] = md5
        recalc_state["processed"] = map_index
        try:
            map_affected: set[int] = set()
            outdated = [
                score for score in map_scores
                if score.status != ScoreStatus.FAILED and score.pp_version != current_version
            ]

            # recalc pp for outdated scores in parallel
            results = await asyncio.gather(*(_calculate_pp(score_service, processor_client, score) for score in outdated))
            for score, pp_attrs in zip(outdated, results):
                if pp_attrs is not None:
                    score.pp = pp_attrs.total
                    score.pp_version = pp_attrs.pp_version
                    recalculed_scores += 1
                    map_affected.add(score.player_id)

            # recompute per-map placements: one BEST per player (highest pp), others SUBMITTED
            old_status = {score.id: score.status for score in map_scores}
            active = [score for score in map_scores if score.status != ScoreStatus.FAILED]
            active.sort(key=lambda score: score.pp or 0.0, reverse=True)
            seen_players: set[int] = set()
            for score in active:
                if score.player_id not in seen_players:
                    score.status = ScoreStatus.BEST
                    seen_players.add(score.player_id)
                else:
                    score.status = ScoreStatus.SUBMITTED

            # players whose status changed need stats too
            for score in map_scores:
                if old_status[score.id] != score.status:
                    map_affected.add(score.player_id)

            await session.commit()
            affected_player_ids.update(map_affected)

            if map_index:
                logger.info("Processed maps: %d/%d", map_index, total_maps)
                _log_state_if_needed()

        except Exception:
            logger.exception("Failed to process map %s during recalc", md5)
            await session.rollback()

    logger.info("Recalculated %d scores across %d maps.", recalculed_scores, total_maps)
    recalc_state["current"] = None
    _log_state_if_needed(force=True)
    return recalculed_scores, affected_player_ids


async def update_affected_stats(player_service: PlayerService, player_repository: PlayerRepository, player_ids: set[int]) -> int:
    if not player_ids:
        return 0
    logger.info("Updating stats for %d affected players...", len(player_ids))
    updated = 0

    # update state
    recalc_state["phase"] = "update_stats"
    recalc_state["processed"] = 0
    recalc_state["total"] = len(player_ids)

    for i, pid in enumerate(player_ids, 1):
        recalc_state["current"] = pid
        recalc_state["processed"] = i
        try:
            # plain repo lookup: leaderboard placement / storage lookups are not needed for stats
            player = await player_repository.from_uid(pid)
            if player:
                await player_service.update_stats(player)
                updated += 1
            if i % 50 == 0:
                logger.info("Stats progress: %d/%d", i, len(player_ids))
                _log_state_if_needed()
        except Exception:
            logger.exception("Failed to update stats for player %d", pid)

    logger.info("Updated stats for %d/%d players.", updated, len(player_ids))
    recalc_state["current"] = None
    _log_state_if_needed(force=True)
    return updated


async def recalc(app_instance):
    start = time.perf_counter()
    logger.info("=== Score recalculation started ===")

    # initialize state
    recalc_state["phase"] = "start"
    recalc_state["current"] = None
    recalc_state["processed"] = 0
    recalc_state["total"] = 0
    _log_state_if_needed(force=True)

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

    score_service = ScoreService(score_repository, player_service, beatmap_service, processor_client)  # BeatmapService will be set later

    current_version = await processor_client.get_pp_version()
    if not current_version:
        logger.error("Failed to get pp_version from processor. Aborting recalc.")
        return

    logger.info("Current pp_version: %s", current_version)

    # await recalc_beatmaps(beatmap_service, current_version)
    _, affected_players = await recalc_scores(score_service, processor_client, score_repository, current_version)
    await update_affected_stats(player_service, player_repository, affected_players)

    # finalize state
    recalc_state["phase"] = "finished"
    recalc_state["current"] = None
    recalc_state["processed"] = 0
    recalc_state["total"] = 0
    _log_state_if_needed(force=True)

    elapsed = time.perf_counter() - start
    logger.info("=== Recalculation finished in %.2fs ===", elapsed)


async def compose(app_instance) -> tuple[Callable, dict]:
    return recalc, app_instance
