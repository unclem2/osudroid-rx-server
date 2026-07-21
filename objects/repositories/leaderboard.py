from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from objects.models.player import PlayerModel
from objects.schemas.player import PlayerSchema
from objects.schemas.stats import StatsSchema


class LeaderboardRepository:  
    def __init__(self, session: AsyncSession,redis: Redis) -> None:
        self.session = session
        self.redis = redis

    async def get_leaderboard_placement(self, player: PlayerModel) -> tuple[int, int, int, int]:
        """Get leaderboard ranking of the player.

        Returns:
            tuple[int, int, int, int]: pp rank, score rank, country pp rank,
                and country score rank.
        """
        async with self.redis.pipeline() as pipe:
            await pipe.zrevrank("main:leaderboard:pp", str(player.id))
            await pipe.zrevrank("main:leaderboard:score", str(player.id))
            await pipe.zrevrank(f"main:leaderboard:{player.country}:pp", str(player.id))
            await pipe.zrevrank(f"main:leaderboard:{player.country}:score", str(player.id))
            pp_rank, score_rank, country_pp_rank, country_score_rank = await pipe.execute()

        if pp_rank is None:
            pp_rank = -1
        if score_rank is None:
            score_rank = -1
        if country_pp_rank is None:
            country_pp_rank = -1
        if country_score_rank is None:
            country_score_rank = -1

        return int(pp_rank) + 1, int(score_rank) + 1, int(country_pp_rank) + 1, int(country_score_rank) + 1

    async def set_leaderboard_placement(self, player: PlayerModel) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.zadd("main:leaderboard:pp", {str(player.id): float(player.stats.pp)})
            await pipe.zadd("main:leaderboard:score", {str(player.id): float(player.stats.ranked_score)})
            await pipe.zadd(f"main:leaderboard:{player.country}:pp", {str(player.id): float(player.stats.pp)})
            await pipe.zadd(f"main:leaderboard:{player.country}:score", {str(player.id): float(player.stats.ranked_score)})
            await pipe.execute()

    async def get_leaderboard(self, order_by: str = "pp", country: str | None = None, limit: int = 100, offset: int = 0):
        redis_key = f"main:leaderboard:{order_by}"
        if country:
            redis_key = f"main:leaderboard:{country}:{order_by}"
        player_ids = await self.redis.zrevrange(redis_key, offset, offset + limit - 1)

        return player_ids

    async def get_leaderboard_count(self, order_by: str = "pp", country: str | None = None) -> int:
        redis_key = f"main:leaderboard:{order_by}"
        if country:
            redis_key = f"main:leaderboard:{country}:{order_by}"
        return await self.redis.zcard(redis_key)

    async def get_player_count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(PlayerSchema))
        return result.scalar_one()

    async def get_countries_list(self) -> list:

        stmt = select(PlayerSchema.country).distinct()
        countries_list = await self.session.execute(stmt)
        return countries_list.scalars().all()
