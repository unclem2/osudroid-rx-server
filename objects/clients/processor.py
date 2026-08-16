import asyncio
import logging
import urllib.parse
from typing import Any

import aiohttp

from config import Config
from objects.models.beatmap import BeatmapModel
from objects.models.processor.input.calculate_score import (
    ProcessorCalculateRequestModel,
)
from objects.models.processor.output.beatmap import ProcessorBeatmapModel
from objects.models.processor.output.performance_attrs import (
    ProcessorPerformanceAttributesModel,
)
from objects.models.processor.output.score import ProcessorScoreModel
from objects.models.score import ScoreModel

log = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (
    aiohttp.ClientError,
    ConnectionResetError,
    BrokenPipeError,
    asyncio.TimeoutError,
)

_MAX_RETRIES = 3

_session: aiohttp.ClientSession | None = None
_base_url: str = ""


def _reset_session() -> None:
    """Invalidate the shared session so the next call creates a fresh one."""
    global _session
    if _session is not None and not _session.closed:
        try:
            loop = _session.loop
            if loop.is_running():
                loop.create_task(_session.close())
            else:
                _session.close()
        except Exception:
            pass
    _session = None


def _is_unix_socket(url: str) -> bool:
    return urllib.parse.urlparse(url).scheme == "unix"


def _get_session() -> aiohttp.ClientSession:
    """Return a process-wide shared session with a reused connection pool."""
    global _session
    if _session is None or _session.closed:
        if _is_unix_socket(_base_url):
            socket_path = urllib.parse.urlparse(_base_url).path
            connector = aiohttp.UnixConnector(path=socket_path)
        else:
            connector = aiohttp.TCPConnector(
                keepalive_timeout=300,
                enable_cleanup_closed=True,
            )
        timeout = aiohttp.ClientTimeout(total=120)
        _session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return _session


class ProcessorClient:
    def __init__(self, config: Config):
        global _base_url
        self.base_url = config.processor_url
        _base_url = self.base_url

    def _make_model(self, data: dict) -> BeatmapModel | None:
        model = ProcessorBeatmapModel.model_validate(data)
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

    async def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> Any:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                session = _get_session()
                async with session.request(method, url, **kwargs) as response:
                    if response.status != 200:
                        return None
                    return await response.json()
            except _RETRYABLE_ERRORS as exc:
                if attempt < _MAX_RETRIES:
                    log.warning(
                        "Processor request failed (%s), attempt %d/%d: %s",
                        url, attempt + 1, _MAX_RETRIES, exc,
                    )
                    _reset_session()
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    log.error(
                        "Processor request failed after %d attempts (%s): %s",
                        _MAX_RETRIES + 1, url, exc,
                    )
                    return None

    async def id_get_beatmap(self, beatmap_id: int) -> BeatmapModel | None:
        url = f"{self.base_url}/api/beatmap/get_beatmap/{beatmap_id}"
        data = await self._request_with_retry("GET", url)
        if data is None:
            return None
        return self._make_model(data)

    async def md5_get_beatmap(self, md5: str) -> BeatmapModel | None:
        url = f"{self.base_url}/api/beatmap/get_beatmap/md5/{md5}"
        data = await self._request_with_retry("GET", url)
        if data is None:
            return None
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
        data = await self._request_with_retry("POST", url, json=calc_req_model.model_dump())
        if data is None:
            return None
        response_model = ProcessorScoreModel.model_validate(data)
        return response_model.pp_attributes

    async def get_pp_version(self):
        url = f"{self.base_url}/metadata/pp_version"
        return await self._request_with_retry("GET", url)
