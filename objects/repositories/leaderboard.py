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
            await pipe.zadd("main:leaderboard:playcount", {str(player.id): float(player.stats.playcount)})
            await pipe.zadd("main:leaderboard:accuracy", {str(player.id): float(player.stats.accuracy)})
            await pipe.zadd(f"main:leaderboard:{player.country}:pp", {str(player.id): float(player.stats.pp)})
            await pipe.zadd(f"main:leaderboard:{player.country}:score", {str(player.id): float(player.stats.ranked_score)})
            await pipe.zadd(f"main:leaderboard:{player.country}:playcount", {str(player.id): float(player.stats.playcount)})
            await pipe.zadd(f"main:leaderboard:{player.country}:accuracy", {str(player.id): float(player.stats.accuracy)})
            stat_leaderboards = {
                "h300": player.stats.h300 + player.stats.hgeki,
                "h100": player.stats.h100 + player.stats.hkatsu,
                "h50": player.stats.h50,
                "hmiss": player.stats.hmiss,
                "rank_xh": player.stats.rank_xh,
                "rank_x": player.stats.rank_x,
                "rank_sh": player.stats.rank_sh,
                "rank_s": player.stats.rank_s,
                "rank_a": player.stats.rank_a,
                "rank_b": player.stats.rank_b,
                "rank_c": player.stats.rank_c,
                "rank_d": player.stats.rank_d,
            }
            for name, value in stat_leaderboards.items():
                await pipe.zadd(f"main:leaderboard:{name}", {str(player.id): float(value)})
                await pipe.zadd(f"main:leaderboard:{player.country}:{name}", {str(player.id): float(value)})
            await pipe.execute()

    async def get_extra_stat_ranks(self, player: PlayerModel) -> dict[str, int]:
        names = (
            "playcount", "accuracy", "h300", "h100", "h50", "hmiss",
            "rank_xh", "rank_x", "rank_sh", "rank_s", "rank_a",
            "rank_b", "rank_c", "rank_d",
        )
        async with self.redis.pipeline() as pipe:
            for name in names:
                await pipe.zrevrank(f"main:leaderboard:{name}", str(player.id))
            ranks = await pipe.execute()

        return {
            name: (int(rank) + 1 if rank is not None else 0)
            for name, rank in zip(names, ranks)
        }

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
