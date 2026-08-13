import pathlib

import aiohttp
from ossapi import OssapiAsync

from config import Config
from objects.clients.processor import ProcessorClient
from objects.models.beatmap import BeatmapModel
from objects.repositories.beatmap import BeatmapRepository
from objects.schemas.beatmap import RankedStatus


class BeatmapService:
    def __init__(self, repository: BeatmapRepository, config: Config, processor_client: ProcessorClient, osu_api_client: OssapiAsync) -> None:
        self.repository = repository
        self.processor_client = processor_client
        self.config = config
        self.osu_api_client = osu_api_client

    async def from_md5(self, md5: str) -> BeatmapModel | None:
        if map := await self.repository.from_md5(md5):
            return map
        return await self.from_md5_api(md5)

    async def from_id(self, beatmap_id: int) -> BeatmapModel | None:
        if map := await self.repository.from_id(beatmap_id):
            return map
        return await self.from_id_api(beatmap_id)

    async def from_md5_api(self, md5: str) -> BeatmapModel | None:
        if map := await self.processor_client.md5_get_beatmap(md5):
            await self.repository.save(map)
            await self.download(map)
            return map
        return None

    async def from_id_api(self, beatmap_id: int) -> BeatmapModel | None:
        if map := await self.processor_client.id_get_beatmap(beatmap_id):
            await self.repository.save(map)
            await self.download(map)
            return map
        return None

    async def change_ranked_status(self, beatmap: BeatmapModel, status: RankedStatus) -> None:
        await self.repository.change_ranked_status(beatmap, status)

    async def update_wip_maps(self):
        beatmaps = await self.repository.get_wip_maps()
        for beatmap in beatmaps:
            status = await self.get_bancho_ranked_status(beatmap)
            await self.change_ranked_status(beatmap, status)

    async def get_bancho_ranked_status(self, beatmap: BeatmapModel) -> RankedStatus:
       map = await self.osu_api_client.beatmap(checksum=beatmap.md5)
       return RankedStatus(map.status)

    async def download(self, beatmap: BeatmapModel) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://old.ppy.sh/osu/{beatmap.id}") as response:
                if response.status != 200:
                    return
                content = await response.text()

        pathlib.Path(f"{self.config.maps_folder}{beatmap.id}.osu").write_text(content, encoding="utf-8")

    async def recalc_get(self, beatmap_model: BeatmapModel) -> BeatmapModel | None:
        beatmap = await self.processor_client.md5_get_beatmap(beatmap_model.md5)
        if beatmap:
            await self.repository.save(beatmap)
            return beatmap
        return None
