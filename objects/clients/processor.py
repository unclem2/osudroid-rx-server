import aiohttp

from config import Config
from objects.models.beatmap import BeatmapModel
from objects.models.processor.input.calculate_score import (
    ProcessorCalculateRequestModel,
)
from objects.models.processor.output.performance_attrs import (
    ProcessorPerformanceAttributesModel,
)
from objects.models.processor.output.score import ProcessorScoreModel
from objects.models.score import ScoreModel


class ProcessorClient:
    def __init__(self, config: Config):
        self.base_url = config.processor_url

    def _make_model(self, data: dict) -> BeatmapModel:
        model = BeatmapModel.model_validate(data)
        attributes = data.get("attributes", {})
        star = attributes.get("star", 0.0)
        model.ar = attributes.get("ar", 0.0)
        model.cs = attributes.get("cs", 0.0)
        model.hp = attributes.get("hp", 0.0)
        model.od = attributes.get("od", 0.0)
        model.star = star.get("total", 0.0)
        return model

    async def id_get_beatmap(self, beatmap_id: int) -> BeatmapModel | None:
        url = f"{self.base_url}/beatmap/{beatmap_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.json()

        return self._make_model(data)

    async def md5_get_beatmap(self, md5: str) -> BeatmapModel | None:
        url = f"{self.base_url}/beatmap/md5/{md5}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.json()

        return self._make_model(data)

    async def calculate_score(self, model: ScoreModel) -> ProcessorPerformanceAttributesModel | None:
        url = f"{self.base_url}/api/calculate/score"
        calc_req_model = ProcessorCalculateRequestModel(
            md5=model.md5,
            miss=model.hmiss,
            combo=model.max_combo,
            h300=model.h300,
            h100=model.h100,
            h50=model.h50,
            hgeki=model.hgeki,
            hkatsu=model.hkatsu,
            slidertickhits=model.slidertickhits,
            sliderendhits=model.sliderendhits,
            mods=model.mods.as_calculable_mods,
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=calc_req_model.model_dump()) as response:
                if response.status != 200:
                    return None
                data = await response.json()

        response_model = ProcessorScoreModel.model_validate(data)

        return response_model.pp_attributes
