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
        cached_beatmap = await self.redis.get(f"main:beatmap:md5:{md5}")
        if cached_beatmap:
            model = BeatmapModel.model_validate_json(cached_beatmap)
            if model.md5 == md5:
                return model

        result = await self.session.execute(
            select(BeatmapSchema).where(BeatmapSchema.md5 == md5),
        )
        beatmap = result.scalar_one_or_none()

        model = self._serizalize(beatmap) if beatmap else None
        if model:
            payload = model.model_dump_json()
            await self.redis.set(f"main:beatmap:md5:{md5}", ex=3600, value=payload)
            await self.redis.set(f"main:beatmap:id:{model.id}", ex=3600, value=payload)
        return model

    async def from_id(self, beatmap_id: int) -> BeatmapModel | None:
        cached_beatmap = await self.redis.get(f"main:beatmap:id:{beatmap_id}")
        if cached_beatmap:
            model = BeatmapModel.model_validate_json(cached_beatmap)
            if model.id == beatmap_id:
                return model

        beatmap = await self.session.get(BeatmapSchema, beatmap_id)

        model = self._serizalize(beatmap) if beatmap else None
        if model:
            payload = model.model_dump_json()
            await self.redis.set(f"main:beatmap:id:{beatmap_id}", ex=3600, value=payload)
            await self.redis.set(f"main:beatmap:md5:{model.md5}", ex=3600, value=payload)
        return model

    async def change_ranked_status(
        self, beatmap: BeatmapModel, status: RankedStatus
    ) -> None:
        schema = await self.session.get(BeatmapSchema, beatmap.id)
        if not schema:
            return
        schema.status = status
        await self.session.commit()

        beatmap.status = status
        payload = beatmap.model_dump_json()
        await self.redis.set(f"main:beatmap:md5:{beatmap.md5}", ex=3600, value=payload)
        await self.redis.set(f"main:beatmap:id:{beatmap.id}", ex=3600, value=payload)

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
        # md5 карты может измениться при апдейте (from_id_api/recalc пишут ту же
        # строку по id), поэтому снимаем и ключ прежнего md5, а не только нового.
        previous_md5 = await self.session.scalar(
            select(BeatmapSchema.md5).where(BeatmapSchema.id == beatmap.id),
        )

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

        stale_keys = [f"main:beatmap:id:{beatmap.id}", f"main:beatmap:md5:{beatmap.md5}"]
        if previous_md5 and previous_md5 != beatmap.md5:
            stale_keys.append(f"main:beatmap:md5:{previous_md5}")
        await self.redis.delete(*stale_keys)
