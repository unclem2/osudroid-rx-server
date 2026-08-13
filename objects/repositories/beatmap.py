from ossapi import BeatmapsetStatus
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from objects.enums.ranked_status import RankedStatus
from objects.models.beatmap import BeatmapModel
from objects.schemas.beatmap import BeatmapSchema


class BeatmapRepository:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    def _serizalize(self, beatmap: BeatmapSchema) -> BeatmapModel:
        return BeatmapModel.model_validate(beatmap)

    def _deserialize(self, model: BeatmapModel) -> BeatmapSchema:
        return BeatmapSchema(**model.model_dump())

    async def from_md5(self, md5: str) -> BeatmapModel | None:
        cached_beatmap = await self.redis.get(f"main:beatmap:{md5}")
        if cached_beatmap:
            return BeatmapModel.model_validate_json(cached_beatmap)

        result = await self.session.execute(
            select(BeatmapSchema).where(BeatmapSchema.md5 == md5),
        )
        beatmap = result.scalar_one_or_none()

        model = self._serizalize(beatmap) if beatmap else None
        if model:
            await self.redis.set(f"main:beatmap:{md5}", ex=3600, value=model.model_dump_json())
            await self.redis.set(f"main:beatmap:{model.id}", ex=3600, value=model.model_dump_json())
        return model

    async def from_id(self, beatmap_id: int) -> BeatmapModel | None:
        cached_beatmap = await self.redis.get(f"main:beatmap:{beatmap_id}")
        if cached_beatmap:
            return BeatmapModel.model_validate_json(cached_beatmap)

        beatmap = await self.session.get(BeatmapSchema, beatmap_id)

        model = self._serizalize(beatmap) if beatmap else None
        if model:
            await self.redis.set(f"main:beatmap:{beatmap_id}", ex=3600, value=model.model_dump_json())
            await self.redis.set(f"main:beatmap:{model.md5}", ex=3600, value=model.model_dump_json())
        return model

    async def change_ranked_status(self, beatmap: BeatmapModel, status: RankedStatus) -> None:
        beatmap.status = status
        await self.session.commit()

        await self.redis.set(f"main:beatmap:{beatmap.md5}", ex=3600, value=beatmap.model_dump_json())
        await self.redis.set(f"main:beatmap:{beatmap.id}", ex=3600, value=beatmap.model_dump_json())

    async def get_wip_maps(self) -> list[BeatmapModel]:
        result = await self.session.execute(
            select(BeatmapSchema).where(BeatmapSchema.status.in_([RankedStatus.Pending, RankedStatus.Qualified, RankedStatus.WIP]))
        )
        beatmaps = result.scalars().all()
        return [self._serizalize(beatmap) for beatmap in beatmaps]

    async def get_outdated(self, current_version: str) -> list[BeatmapModel]:
        result = await self.session.execute(
            select(BeatmapSchema).where(BeatmapSchema.pp_version != current_version),
        )
        beatmaps = result.scalars().all()
        return [self._serizalize(beatmap) for beatmap in beatmaps]

    async def save(self, beatmap: BeatmapModel) -> None:
        stmt = (
            insert(BeatmapSchema)
            .values(
                id=beatmap.id,
                set_id=beatmap.set_id,
                md5=beatmap.md5,
                artist=beatmap.artist,
                title=beatmap.title,
                version=beatmap.version,
                creator=beatmap.creator,
                last_update=beatmap.last_update,
                total_length=beatmap.total_length,
                max_combo=beatmap.max_combo,
                bpm=beatmap.bpm,
                status=beatmap.status,
                ar=beatmap.ar,
                cs=beatmap.cs,
                od=beatmap.od,
                hp=beatmap.hp,
                star=beatmap.star,
                pp_version=beatmap.pp_version,
            )
            .on_conflict_do_update(
                index_elements=[BeatmapSchema.id],
                set_={
                    "set_id": beatmap.set_id,
                    "md5": beatmap.md5,
                    "artist": beatmap.artist,
                    "title": beatmap.title,
                    "version": beatmap.version,
                    "creator": beatmap.creator,
                    "last_update": beatmap.last_update,
                    "total_length": beatmap.total_length,
                    "max_combo": beatmap.max_combo,
                    "bpm": beatmap.bpm,
                    "ar": beatmap.ar,
                    "cs": beatmap.cs,
                    "od": beatmap.od,
                    "hp": beatmap.hp,
                    "star": beatmap.star,
                    "pp_version": beatmap.pp_version,
                },
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
