import aiohttp

from config import Config
from objects.models.beatmap import BeatmapModel
from objects.models.processor.input.calculate_score import (
    ProcessorCalculateRequestModel,
)
from objects.models.processor.output.performance_attrs import (
    ProcessorPerformanceAttributesModel,
)
from objects.models.processor.output.beatmap import ProcessorBeatmapModel
from objects.models.processor.output.score import ProcessorScoreModel
from objects.models.score import ScoreModel


_session: aiohttp.ClientSession | None = None


def _get_session() -> aiohttp.ClientSession:
    """Return a process-wide shared session with a reused connection pool."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


class ProcessorClient:
    def __init__(self, config: Config):
        self.base_url = config.processor_url

    def _make_model(self, data: dict) -> BeatmapModel | None:
        model = ProcessorBeatmapModel.model_validate(data)
        # attributes = data.get("attributes", {})
        # star = attributes.get("star", 0.0)
        # model.ar = attributes.get("ar", 0.0)
        # model.cs = attributes.get("cs", 0.0)
        # model.hp: Unknown = attributes.get("hp", 0.0)
        # model.od = attributes.get("od", 0.0)
        # model.star = star.get("total", 0.0)
        beatmap_model = BeatmapModel(
            id=model.id,
            set_id=model.set_id,
            md5=model.md5,
            artist=model.artist,
            title=model.title,
            version=model.version,
            creator=model.creator,
            last_update=model.last_update,
            total_length=model.total_length,
            max_combo=model.max_combo,
            bpm=model.bpm,
            ar=model.attributes.ar if model.attributes else 0.0,
            cs=model.attributes.cs if model.attributes else 0.0,
            hp=model.attributes.hp if model.attributes else 0.0,
            od=model.attributes.od if model.attributes else 0.0,
            star=model.star.total if model.star else 0.0,
            pp_version=model.star.pp_version if model.star else "",
        )
        return beatmap_model

    async def id_get_beatmap(self, beatmap_id: int) -> BeatmapModel | None:
        url = f"{self.base_url}/api/beatmap/get_beatmap/{beatmap_id}"
        async with _get_session().get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()

        return self._make_model(data)

    async def md5_get_beatmap(self, md5: str) -> BeatmapModel | None:
        url = f"{self.base_url}/api/beatmap/get_beatmap/md5/{md5}"
        async with _get_session().get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()

        return self._make_model(data)

    async def calculate_score(self, model: ScoreModel) -> ProcessorPerformanceAttributesModel | None:
        url = f"{self.base_url}/api/calculate/score/"
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
        async with _get_session().post(url, json=calc_req_model.model_dump()) as response:
            if response.status != 200:
                return None
            data = await response.json()

        response_model = ProcessorScoreModel.model_validate(data)

        return response_model.pp_attributes

    async def get_pp_version(self):
        url = f"{self.base_url}/metadata/pp_version"
        async with _get_session().get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()

        return data