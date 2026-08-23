import asyncio
import logging
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


class ProcessorClient:
    def __init__(self, config: Config):
        raw_url = config.processor_url.rstrip("/")

        # Определяем, является ли адрес Unix-сокетом
        if raw_url.startswith("unix://") or raw_url.startswith("/"):
            self._socket_path: str | None = raw_url.removeprefix("unix://")
            self.base_url = "http://localhost"
        else:
            self._socket_path = None
            self.base_url = raw_url

        self._session: aiohttp.ClientSession | None = None

    def _create_connector(self) -> aiohttp.BaseConnector:
        if self._socket_path:
            return aiohttp.UnixConnector(path=self._socket_path)
        return aiohttp.TCPConnector(
            keepalive_timeout=300,
            enable_cleanup_closed=True,
        )

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                connector=self._create_connector(),
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        """Закрытие сессии при завершении работы."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _reset_session(self) -> None:
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception:
                pass
        self._session = None

    def _make_model(self, data: dict) -> BeatmapModel:
        model = ProcessorBeatmapModel.model_validate(data)
        attrs = model.attributes
        star = model.star

        return BeatmapModel(
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
            ar=attrs.ar if attrs else 0.0,
            cs=attrs.cs if attrs else 0.0,
            hp=attrs.hp if attrs else 0.0,
            od=attrs.od if attrs else 0.0,
            star=star.total if star else 0.0,
            pp_version=star.pp_version if star else "",
        )

    async def _request_with_retry(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                session = self._get_session()
                async with session.request(method, endpoint, **kwargs) as response:
                    if response.status != 200:
                        log.warning(
                            "Processor API non-200 status [%s %s]: %s",
                            method, endpoint, response.status,
                        )
                        return None
                    return await response.json()
            except _RETRYABLE_ERRORS as exc:
                if attempt < _MAX_RETRIES:
                    log.warning(
                        "Processor request failed (%s), attempt %d/%d: %s",
                        endpoint, attempt + 1, _MAX_RETRIES, exc,
                    )
                    await self._reset_session()
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    log.error(
                        "Processor request failed after %d attempts (%s): %s",
                        _MAX_RETRIES + 1, endpoint, exc,
                    )
                    return None

    async def id_get_beatmap(self, beatmap_id: int) -> BeatmapModel | None:
        data = await self._request_with_retry("GET", f"/api/beatmap/get_beatmap/{beatmap_id}")
        return self._make_model(data) if data else None

    async def md5_get_beatmap(self, md5: str) -> BeatmapModel | None:
        data = await self._request_with_retry("GET", f"/api/beatmap/get_beatmap/md5/{md5}")
        return self._make_model(data) if data else None

    async def calculate_score(self, model: ScoreModel) -> ProcessorPerformanceAttributesModel | None:
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

        data = await self._request_with_retry(
            "POST",
            "/api/calculate/score/",
            json=calc_req_model.model_dump(mode="json"),
        )
        if not data:
            return None

        response_model = ProcessorScoreModel.model_validate(data)
        return response_model.pp_attributes

    async def get_pp_version(self) -> Any | None:
        return await self._request_with_retry("GET", "/metadata/pp_version")