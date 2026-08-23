import asyncio
import logging

from objects.clients.processor import ProcessorClient
from objects.db import sessionmaker
from objects.enums.score_status import ScoreStatus
from objects.models.score import ScoreModel
from objects.repositories.beatmap import BeatmapRepository
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService
from objects.services.score import ScoreService
from config import Config

logger = logging.getLogger(__name__)

_PROCESSOR_CONCURRENCY = 8


def is_ranked(score: ScoreModel) -> bool:
    if score.mods.get_mod("RX") is None:
        return False
    if score.mods.get_mod("WU") or score.mods.get_mod("WD") or score.mods.get_mod("AP"):
        return False
    if (
        da := score.mods.get_mod("DA")
    ) and (
        setting := da.settings.get_setting("cs")
        or da.settings.get_setting("od")
    ) and setting.value is not None:
        return False
    return True


class RecalcService:
    def __init__(self, processor_client: ProcessorClient, config, osu_api_client, redis):
        self.processor_client = processor_client
        self.config = config
        self.osu_api_client = osu_api_client
        self.redis = redis
        self._semaphore = asyncio.Semaphore(_PROCESSOR_CONCURRENCY)

    def _create_services(self, session) -> tuple[ScoreService, BeatmapService, PlayerService, ScoreRepository, BeatmapRepository]:
        score_repo = ScoreRepository(session, self.redis)
        beatmap_repo = BeatmapRepository(session, self.redis)
        player_repo = PlayerRepository(session, self.redis)
        lb_repo = LeaderboardRepository(session, self.redis)
        player_storage = PlayerStorage(session, self.redis)

        player_service = PlayerService(player_repo, lb_repo, player_storage, score_repo)
        beatmap_service = BeatmapService(beatmap_repo, self.config, self.processor_client, self.osu_api_client)
        score_service = ScoreService(score_repo, player_service, beatmap_service, self.processor_client)

        return score_service, beatmap_service, player_service, score_repo, beatmap_repo

    @staticmethod
    async def get_recalc_state() -> dict[str, int]:
        async with sessionmaker() as session:
            score_repo = ScoreRepository(session, None)
            processor_client = ProcessorClient(Config())
            pp_version = await processor_client.get_pp_version()

            outdated_scores_count = await score_repo.outdated_count(pp_version)
            total_scores_count = await score_repo.total_count()
            return {
                "outdated_scores": outdated_scores_count,
                "total_scores": total_scores_count,
            }


    async def _calculate_pp(self, score: ScoreModel):
        async with self._semaphore:
            if is_ranked(score):
                return await self.processor_client.calculate_score(score)
        return None

    async def get_outdated_scores(self, current_version: str) -> dict[str, list[ScoreModel]]:
        async with sessionmaker() as session:
            score_service, _, _, _, _ = self._create_services(session)
            return await score_service.get_outdated(current_version)

    async def get_outdated_beatmaps(self, current_version: str):
        async with sessionmaker() as session:
            _, _, _, _, beatmap_repo = self._create_services(session)
            return await beatmap_repo.get_outdated(current_version)

    async def recalc_score(self, score_id: int) -> ScoreModel | None:
        async with sessionmaker() as session:
            score_service, _, _, _, _ = self._create_services(session)

            score = await score_service.from_id(score_id)
            if not score:
                return None

            pp_attrs = await self._calculate_pp(score)
            if pp_attrs:
                score.pp = pp_attrs.total
                score.pp_version = pp_attrs.pp_version
            else:
                score.pp = 0.0

            score.status = await score_service.calc_status(score)
            if score.status == ScoreStatus.UNRANKED:
                score.pp = 0.0

            await score_service.update(score)
            return score

    async def recalc_beatmap(self, md5: str, scores: list[ScoreModel] | None, current_version: str = "") -> set[int]:
        """Recalculate all scores for a beatmap. Returns affected player IDs."""
        async with sessionmaker() as session:
            score_service, beatmap_service, _, score_repo, _ = self._create_services(session)

            all_scores = await score_service.scores_by_md5(md5) if scores is None else scores
            if not all_scores:
                return set()

            beatmap = await beatmap_service.from_md5_api(md5)
            if not beatmap:
                score_updates = {}
                affected = set()
                for score in all_scores:
                    score_updates.setdefault(score.id, {})
                    affected.add(score.player_id)
                    score_updates[score.id]["status"] = ScoreStatus.DELISTED
                await score_repo.batch_update(score_updates)
                return affected

            # Calculate PP
            results = await asyncio.gather(
                *(self._calculate_pp(score) for score in all_scores),
                return_exceptions=True,
            )
            score_updates: dict[int, dict] = {}
            for score, result in zip(all_scores, results):
                if isinstance(result, BaseException):
                    logger.warning("PP calc failed for score %d: %s", score.id, result)
                    # score_updates[score.id]["status"] = ScoreStatus.DELISTED
                    continue
                if result is not None:
                    score_updates.setdefault(score.id, {})
                    score_updates[score.id]["pp"] = result.total
                    score_updates[score.id]["pp_version"] = result.pp_version

            # Determine statuses
            old_status = {s.id: s.status for s in all_scores}
            affected: set[int] = set()

            ranked_active = []
            for score in all_scores:
                if not is_ranked(score):
                    new_status = ScoreStatus.UNRANKED
                    if score.status != new_status:
                        score_updates.setdefault(score.id, {})
                        score_updates[score.id]["status"] = new_status
                    score_updates.setdefault(score.id, {})
                    score_updates[score.id]["pp"] = 0
                    if current_version:
                        score_updates[score.id]["pp_version"] = current_version
                    continue
                ranked_active.append(score)

            ranked_active.sort(
                key=lambda s: score_updates.get(s.id, {}).get("pp", s.pp or 0.0),
                reverse=True,
            )
            seen_players: set[int] = set()
            for score in ranked_active:
                if score.player_id not in seen_players:
                    new_status = ScoreStatus.BEST
                    seen_players.add(score.player_id)
                else:
                    new_status = ScoreStatus.SUBMITTED
                if old_status[score.id] != new_status:
                    score_updates.setdefault(score.id, {})
                    score_updates[score.id]["status"] = new_status

            for score in all_scores:
                current_new_status = score_updates.get(score.id, {}).get("status", old_status[score.id])
                if old_status[score.id] != current_new_status:
                    affected.add(score.player_id)

            if score_updates:
                await score_repo.batch_update(score_updates)

            return affected

    async def recalc_player(self, player_id: int) -> bool:
        async with sessionmaker() as session:
            _, _, player_service, _, _ = self._create_services(session)

            player = await player_service.from_uid(player_id)
            if not player:
                return False

            await player_service.update_stats(player)
            return True

    async def recalc_all(self) -> None:
        start = asyncio.get_event_loop().time()
        logger.info("=== Recalculation started ===")

        current_version = await self.processor_client.get_pp_version()
        if not current_version:
            logger.error("Failed to get pp_version from processor. Aborting.")
            return

        logger.info("Current pp_version: %s", current_version)

        
        affected_players = await self._recalc_all_scores(current_version)
        await self._update_all_stats(affected_players)
        await self._recalc_all_beatmaps(current_version)

        elapsed = asyncio.get_event_loop().time() - start
        logger.info("=== Recalculation finished in %.2fs ===", elapsed)

    async def _recalc_all_beatmaps(self, current_version: str) -> None:
        async with sessionmaker() as session:
            _, beatmap_service, _, _, beatmap_repo = self._create_services(session)

            outdated = await beatmap_repo.get_outdated(current_version)
            if not outdated:
                logger.info("All beatmaps are up to date.")
                return

            total = len(outdated)
            logger.info("Found %d outdated beatmaps.", total)

            async def _fetch(beatmap):
                async with self._semaphore:
                    return await self.processor_client.md5_get_beatmap(beatmap.md5)

            fetched = await asyncio.gather(*(_fetch(b) for b in outdated))

            recalculed = 0
            for i, (beatmap, new_beatmap) in enumerate(zip(outdated, fetched), 1):
                if new_beatmap:
                    try:
                        await beatmap_repo.save(new_beatmap)
                        recalculed += 1
                    except Exception:
                        logger.exception("Failed to save beatmap %s", beatmap.md5)
                if i % 50 == 0:
                    logger.info("Beatmaps: %d/%d", i, total)

            logger.info("Recalculated %d/%d beatmaps.", recalculed, total)

    async def _recalc_all_scores(self, current_version: str) -> set[int]:
        by_md5 = await self.get_outdated_scores(current_version)
        if not by_md5:
            logger.info("All scores are up to date.")
            return set()

        total_maps = len(by_md5)
        total_scores = sum(len(v) for v in by_md5.values())
        logger.info("Found %d scores across %d outdated maps.", total_scores, total_maps)

        affected_players: set[int] = set()

        for map_index, (md5, map_scores) in enumerate(by_md5.items(), 1):
            try:
                players = await self.recalc_beatmap(md5, map_scores, current_version)
                affected_players.update(players)
            except Exception:
                logger.exception("Failed to recalc map %s", md5)
            if map_index % 50 == 0:
                logger.info("Scores: %d/%d", map_index, total_maps)

        logger.info("Affected %d players across %d maps.", len(affected_players), total_maps)
        return affected_players

    async def _update_all_stats(self, player_ids: set[int]) -> None:
        if not player_ids:
            return

        logger.info("Updating stats for %d players...", len(player_ids))

        updated = 0
        for i, pid in enumerate(player_ids, 1):
            try:
                if await self.recalc_player(pid):
                    updated += 1
            except Exception:
                logger.exception("Failed to update stats for player %d", pid)
            if i % 50 == 0:
                logger.info("Stats: %d/%d", i, len(player_ids))

        logger.info("Updated stats for %d/%d players.", updated, len(player_ids))
