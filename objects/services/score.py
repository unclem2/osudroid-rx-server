import json
from datetime import datetime

from osudroid_api_wrapper import ModList

from objects.clients.processor import ProcessorClient
from objects.models.beatmap import BeatmapModel
from objects.models.processor.output.performance_attrs import (
    ProcessorPerformanceAttributesModel,
)
from objects.models.score import ScoreModel
from objects.repositories.score import ScoreRepository
from objects.schemas.score import ScoreStatus
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService


class ScoreService:
    def __init__(self, score_repository: ScoreRepository, player_service: PlayerService, beatmap_service: BeatmapService, processor_client: ProcessorClient):
        self.score_repository = score_repository
        self.player_service = player_service
        self.beatmap_service = beatmap_service
        self.processor_client = processor_client

    async def from_id(self, score_id: int) -> ScoreModel | None:
        return await self.score_repository.from_id(score_id)

    async def beatmap_scores(self, beatmap_md5: str, order_by: str = "score") -> list[ScoreModel]:
        return await self.score_repository.beatmap_scores(beatmap_md5, order_by)

    async def player_scores(self, player_id: int, status: str, order_by: str = "date", limit: int = 100) -> list[ScoreModel]:
        return await self.score_repository.player_scores(player_id, status, order_by, limit)

    async def player_top_scores(self, player_id: int, limit: int = 100) -> list[ScoreModel]:
        return await self.score_repository.player_top_scores(player_id, limit)

    async def global_top_scores(self, limit: int = 10) -> list[ScoreModel]:
        return await self.score_repository.global_top_scores(limit)

    async def player_first_places(self, player_id: int, order_by: str = "score", limit: int = 100) -> list[ScoreModel]:
        return await self.score_repository.player_first_places(player_id, order_by, limit)

    async def player_beatmap_scores(self, player_id: int, beatmap_md5: str) -> list[ScoreModel]:
        return await self.score_repository.player_beatmap_scores(player_id, beatmap_md5)

    async def recent_score(self, player_id: int, offset: int = 0) -> ScoreModel | None:
        return await self.score_repository.recent_score(player_id, offset)

    async def from_submit(self, submit_string: str) -> ScoreModel | None:
        score_data = submit_string.split(" ")

        if len(score_data) < 18:
            return None

        score = ScoreModel()

        username = score_data[17]  # legacy 13
        player = await self.player_service.from_username(username)
        if not player:
            return None  # Player not found(pretty much impossible case)

        score.player_id = player.id
        score.player = player

        if player.playing:
            score.md5 = player.playing

        beatmap = await self.beatmap_service.from_md5(score.md5)
        if not beatmap:
            return None  # Beatmap not found

        score.beatmap_id = beatmap.id
        score.beatmap = beatmap

        score.mods = ModList.from_dict(json.loads(score_data[0]))
        score.score, score.max_combo = map(int, score_data[1:3])
        score.grade = score_data[3]
        score.hgeki, score.h300, score.hkatsu, score.h100, score.h50, score.hmiss = map(int, score_data[4:10])
        score.sliderheadhits, score.slidertickhits, score.sliderrepeathits, score.sliderendhits = map(int, score_data[10:14])
        score.accuracy = float(score_data[14]) * 100
        score.date = datetime.fromtimestamp(int(score_data[15]) / 1000)
        score.fc = score_data[16] == "true" or score_data[16] == "1"

        pp_attrs = await self.processor_client.calculate_score(score)
        if pp_attrs:
            score.pp = pp_attrs.total
            score.pp_version = pp_attrs.pp_version
            score.status = await self.calc_status(score)
            if score.status == ScoreStatus.UNRANKED:
                score.pp = 0.0
        else:
            score.pp = 0.0
            score.status = ScoreStatus.SUBMITTED

        return score

    async def save(self, score: ScoreModel) -> ScoreModel:
        return await self.score_repository.save(score)

    async def score_global_placement(self, score: ScoreModel) -> int:
        return await self.score_repository.score_global_placement(score)

    async def calculate(
        self,
        beatmap: BeatmapModel,
        mods: list,
        acc: float | None,
        miss: int | None,
        combo: int | None,
        h300: int | None,
        h100: int | None,
        h50: int | None,
        hgeki: int | None,
        hkatsu: int | None,
        slidertickhits: int | None,
        sliderendhits: int | None,
        sliderheadhits: int | None,
        sliderrepeathits: int | None,
    ) -> ProcessorPerformanceAttributesModel | None:
        model = ScoreModel()
        model.beatmap = beatmap
        model.mods = mods
        model.accuracy = acc
        model.miss = miss
        model.max_combo = combo
        model.h300 = h300
        model.h100 = h100
        model.h50 = h50
        model.hgeki = hgeki
        model.hkatsu = hkatsu
        model.slidertickhits = slidertickhits
        model.sliderendhits = sliderendhits
        model.sliderheadhits = sliderheadhits
        model.sliderrepeathits = sliderrepeathits

        response: ProcessorPerformanceAttributesModel | None = await self.processor_client.calculate_score(model)
        return response

    def is_ranked(self, score: ScoreModel) -> bool:
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
        
    async def calc_status(self, score: ScoreModel) -> ScoreStatus:
        if not self.is_ranked(score):
            return ScoreStatus.UNRANKED
        return await self.score_repository.calc_status(score)