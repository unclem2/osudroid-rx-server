from redis import asyncio
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from objects.enums.submission_status import SubmissionStatus
from objects.models.score import ScoreModel
from objects.schemas.beatmap import BeatmapSchema
from objects.schemas.score import ScoreSchema

ALLOWED_ORDER_BY = {"score", "pp", "date", "accuracy", "max_combo", "id"}


class ScoreRepository:
    def __init__(self, session: AsyncSession, redis: asyncio.Redis) -> None:
        self.session = session
        self.redis = redis

    def _serizalize(self, score: ScoreSchema) -> ScoreModel:
        return ScoreModel.model_validate(score)

    def _deserialize(self, model: ScoreModel) -> ScoreSchema:
        dump = model.db_dump()
        return ScoreSchema(**dump)

    async def from_id(self, score_id: int) -> ScoreModel | None:
        score = await self.session.get(ScoreSchema, score_id)
        return self._serizalize(score) if score else None

    async def beatmap_scores(self, beatmap_md5: str, order_by: str = "score", limit: int = 100) -> list[ScoreModel]:
        if order_by not in ALLOWED_ORDER_BY:
            order_by = "score"
        stmt = (
            select(ScoreSchema)
            .where(ScoreSchema.md5 == beatmap_md5, ScoreSchema.status == SubmissionStatus.BEST)
            .order_by(getattr(ScoreSchema, order_by).desc())
        )

        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def player_scores(self, player_id: int, status: str, order_by: str = "date", limit: int = 100) -> list[ScoreModel]:
        if order_by not in ALLOWED_ORDER_BY:
            order_by = "date"
        stmt = (
            select(ScoreSchema)
            .where(
                ScoreSchema.player_id == player_id,
                ScoreSchema.status == SubmissionStatus.BEST if status == "best" else ScoreSchema.status.in_([SubmissionStatus.BEST, SubmissionStatus.SUBMITTED]),
            ).order_by(getattr(ScoreSchema, order_by).desc())
        )
        if limit != -1:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def player_top_scores(self, player_id: int, limit: int = 100) -> list[ScoreModel]:
        stmt = (
            select(ScoreSchema)
            .where(
                ScoreSchema.player_id == player_id,
                ScoreSchema.status == SubmissionStatus.BEST,
                ScoreSchema.md5.in_(
                    select(BeatmapSchema.md5).where(BeatmapSchema.status.in_([1, 2, 4, 5])),
                ),
            )
            .order_by(ScoreSchema.pp.desc())
        )
        if limit != -1:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def player_first_places(self, player_id: int, order_by: str = "score", limit: int = 100) -> list[ScoreModel]:
        if order_by not in ALLOWED_ORDER_BY:
            order_by = "score"
        maps_played_by_user = (
            select(ScoreSchema.md5)
            .where(
                ScoreSchema.player_id == player_id,
                ScoreSchema.status == SubmissionStatus.BEST,
            )
        )

        maps_lbs = (
            select(ScoreSchema)
            .where(
                and_(
                    ScoreSchema.md5.in_(maps_played_by_user),
                    ScoreSchema.status == SubmissionStatus.BEST,
                ),
            )
        )
        maps_first_places = (
            maps_lbs.order_by(
                ScoreSchema.md5,
                getattr(ScoreSchema, order_by).desc(),
            )
            .distinct(ScoreSchema.md5)
            .subquery()
        )

        fp = aliased(ScoreSchema, maps_first_places)

        user_first_places = (
            select(fp)
            .where(fp.player_id == player_id)
            .order_by(getattr(fp, order_by).desc())
        )
        if limit != -1:
            user_first_places = user_first_places.limit(limit)

        result = await self.session.execute(user_first_places)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def get_outdated(self, current_version: str) -> list[ScoreModel]:
        stmt = select(ScoreSchema).where(ScoreSchema.pp_version != current_version)
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def update_pp(self, score_id: int, pp: float, pp_version: str) -> None:
        score = await self.session.get(ScoreSchema, score_id)
        if score:
            score.pp = pp
            score.pp_version = pp_version
            await self.session.commit()

    async def save(self, score: ScoreModel) -> ScoreModel:
        schema = self._deserialize(score)
        self.session.add(schema)
        await self.session.commit()
        await self.session.refresh(schema)
        return self._serizalize(schema)

    async def update(self, score: ScoreModel) -> ScoreModel:
        schema = await self.session.get(ScoreSchema, score.id)
        if not schema:
            raise ValueError(f"Score with id {score.id} does not exist.")

        for key, value in score.model_dump().items():
            setattr(schema, key, value)

        await self.session.commit()
        return self._serizalize(schema)

    async def calc_status(self, score: ScoreModel) -> SubmissionStatus:

        resp_status = SubmissionStatus.SUBMITTED
        prev_best_query = select(ScoreSchema).where(
            ScoreSchema.player_id == score.player_id,
            ScoreSchema.md5 == score.md5,
            ScoreSchema.status == SubmissionStatus.BEST,
        ).with_for_update()
        response = await self.session.execute(prev_best_query)
        prev_best = response.scalar_one_or_none()
        if prev_best:
            if score.pp > prev_best.pp:
                resp_status = SubmissionStatus.BEST
                prev_best.status = SubmissionStatus.SUBMITTED
                await self.session.commit()
            else:
                resp_status = SubmissionStatus.SUBMITTED
        else:
            resp_status = SubmissionStatus.BEST
        return resp_status

    async def player_beatmap_scores(self, player_id: int, beatmap_md5: str, order_by: str = "local_placement") -> list[ScoreModel]:
        stmt = (
            select(ScoreSchema)
            .where(
                ScoreSchema.player_id == player_id,
                ScoreSchema.md5 == beatmap_md5,
            )
            .order_by(getattr(ScoreSchema, order_by).asc())
        )
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def recent_score(self, player_id: int, offset: int = 0) -> ScoreModel | None:
        stmt = (
            select(ScoreSchema)
            .where(ScoreSchema.player_id == player_id)
            .order_by(ScoreSchema.id.desc())
            .offset(offset)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        score = result.scalar_one_or_none()
        return self._serizalize(score) if score else None

    async def global_top_scores(self, limit: int = 10) -> list[ScoreModel]:
        stmt = (
            select(ScoreSchema)
            .where(
                ScoreSchema.status == SubmissionStatus.BEST,
                ScoreSchema.md5.in_(
                    select(BeatmapSchema.md5).where(BeatmapSchema.status.in_([1, 2, 4, 5])),
                ),
            )
            .order_by(ScoreSchema.pp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return [self._serizalize(score) for score in scores]

    async def score_global_placement(self, score: ScoreModel) -> int:
        if score.status != SubmissionStatus.BEST:
            return 0
        stmt = (
            select(ScoreSchema)
            .where(
                ScoreSchema.md5 == score.md5,
                ScoreSchema.status == SubmissionStatus.BEST,
                ScoreSchema.pp > score.pp,
            )
        )
        result = await self.session.execute(stmt)
        scores = result.scalars().all()
        return len(scores) + 1
