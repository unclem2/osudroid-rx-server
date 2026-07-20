from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from objects.models.player import PlayerModel
from objects.schemas.player import PlayerSchema
from objects.schemas.stats import StatsSchema


class PlayerRepository:  # noqa: PLR0904
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    def _serizalize(self, player: PlayerSchema) -> PlayerModel:
        return PlayerModel.model_validate(player)

    def _deserialize(self, model: PlayerModel) -> PlayerSchema:
        dump = model.db_dump()
        dump["stats"] = StatsSchema(**dump["stats"])
        return PlayerSchema(**dump)

    async def from_uid(self, player_id: int) -> PlayerModel | None:
        cached_player = await self.redis.get(f"main:player:{player_id}:data")
        if cached_player:
            model = PlayerModel.model_validate_json(cached_player)
        if not model:
            player = await self.session.get(PlayerSchema, player_id)
            model = self._serizalize(player) if player else None

        await self.redis.set(f"main:player:{player_id}:data", value=model.model_dump_json()) if model else None
        await self.redis.set(f"main:player:{model.username}:data", value=model.model_dump_json()) if model else None

        if model:
            model.pp_rank, model.score_rank, model.pp_country_rank, model.score_country_rank = await self._get_leaderboard_placement(model)
            model.playing = await self.get_playing(model.id)
            if level := await self.get_level(model.id):
                model.stats.level = level
            else:
                model.stats.level = 0

        return model

    async def from_username(self, username: str) -> PlayerModel | None:
        cached_player = await self.redis.get(f"main:player:{username}:data")
        if cached_player:
            model = PlayerModel.model_validate_json(cached_player)
        if not model:
            player = await self.session.get(PlayerSchema, username)
            model = self._serizalize(player) if player else None

        await self.redis.set(f"main:player:{username}:data", value=model.model_dump_json()) if model else None
        await self.redis.set(f"main:player:{model.id}:data", value=model.model_dump_json()) if model else None

        if model:
            model.pp_rank, model.score_rank, model.pp_country_rank, model.score_country_rank = await self._get_leaderboard_placement(model)
            model.playing = await self.get_playing(model.id)
            if level := await self.get_level(model.id):
                model.stats.level = level
            else:
                model.stats.level = 0
        return model

    async def new(self, username: str, password_hash: str, device_id: str, email_hash: str) -> PlayerModel:
        stmt = (
            insert(PlayerSchema)
            .values(
                username=username,
                password_hash=password_hash,
                device_id=device_id,
                email_hash=email_hash,
            )
            .returning(PlayerSchema)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        player = result.scalar_one()
        model = self._serizalize(player)
        await self.redis.set(f"main:player:{model.id}:data", value=model.model_dump_json())
        await self.redis.set(f"main:player:{model.username}:data", value=model.model_dump_json())
        await self._update_leaderboard(model)
        await self.update_level(model)
        return model

    async def _get_leaderboard_placement(self, player: PlayerModel) -> tuple[int, int, int, int]:
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

    async def _update_leaderboard(self, player: PlayerModel) -> tuple[int, int, int, int]:
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.zadd("main:leaderboard:pp", {str(player.id): float(player.stats.pp)})
            await pipe.zadd("main:leaderboard:score", {str(player.id): float(player.stats.ranked_score)})
            await pipe.zadd(f"main:leaderboard:{player.country}:pp", {str(player.id): float(player.stats.pp)})
            await pipe.zadd(f"main:leaderboard:{player.country}:score", {str(player.id): float(player.stats.ranked_score)})
            await pipe.execute()

        return await self._get_leaderboard_placement(player)

    async def update_player(self, player: PlayerModel) -> None:
        player_schema = self._deserialize(player)
        await self.session.merge(player_schema)
        await self.session.commit()
        await self.redis.set(f"main:player:{player.id}:data", value=player.model_dump_json())
        await self.redis.set(f"main:player:{player.username}:data", value=player.model_dump_json())
        await self._update_leaderboard(player)
        await self.update_level(player)

    async def update_level(self, player: PlayerModel) -> None:
        await self.redis.set(f"main:player:{player.id}:level", player.stats.level)

    async def get_level(self, player_id: int) -> int | None:
        level = await self.redis.get(f"main:player:{player_id}:level")
        return int(level) if level else None

    async def get_password(self, player_id: int) -> str | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.password_hash if player else None

    async def set_password(self, player_id: int, new_password_hash: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.password_hash = new_password_hash
            await self.session.commit()

    async def set_country(self, player_id: int, country: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.country = country
            await self.session.commit()

    async def set_playing(self, player_id: int, md5: str) -> None:
        await self.redis.setex(f"main:player:{player_id}:playing", 600, md5)

    async def get_playing(self, player_id: int) -> str | None:
        playing = await self.redis.get(f"main:player:{player_id}:playing")
        if isinstance(playing, bytes):
            return playing.decode()
        return playing if playing else None

    async def set_uuid(self, player_id: int, uuid: str) -> None:
        await self.redis.set(f"main:player:{player_id}:uuid", uuid)

    async def get_uuid(self, player_id: int) -> str | None:
        uuid = await self.redis.get(f"main:player:{player_id}:uuid")
        if isinstance(uuid, bytes):
            return uuid.decode()
        return uuid if uuid else None

    async def set_last_online(self, player_id: int, timestamp: float) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            await self.redis.setex(f"main:player:{player.id}:last_online", 600, str(timestamp))

    async def get_last_online(self, player_id: int) -> float | None:
        last_online = await self.redis.get(f"main:player:{player_id}:last_online")
        return float(last_online) if last_online else None

    async def set_status(self, player_id: int, status: int) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.status = status
            await self.session.commit()

    async def get_status(self, player_id: int) -> int | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.status if player else None

    async def init_players(self) -> None:
        result = await self.session.execute(select(PlayerSchema).where(PlayerSchema.id > 0))
        players = result.scalars().all()
        async with self.redis.pipeline(transaction=True) as pipe:
            for player in players:
                model = self._serizalize(player)
                await self.update_player(model)
            await pipe.execute()

    async def get_player_count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(PlayerSchema))
        return result.scalar_one()

    async def get_online_player_count(self) -> int:
        keys = await self.redis.keys("main:player:*:playing")
        return len(keys)

    async def change_username(self, player_id: int, new_username: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            old_username = player.username
            player.username = new_username
            await self.session.commit()
            await self.redis.delete(f"main:player:{old_username}")
            await self.redis.delete(f"main:player:{player_id}")
            model = self._serizalize(player)
            await self.redis.set(f"main:player:{new_username}:data", value=model.model_dump_json())
            await self.redis.set(f"main:player:{player_id}:data", value=model.model_dump_json())
        
    async def set_email_hash(self, player_id: int, email_hash: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.email_hash = email_hash
            await self.session.commit()

    async def get_email_hash(self, player_id: int) -> str | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.email_hash if player else None

    async def get_leaderboard(self, order_by: str = "pp", country: str | None = None, limit: int = 100, offset: int = 0) -> list[PlayerModel]:
        redis_key = f"main:leaderboard:{order_by}"
        if country:
            redis_key = f"main:leaderboard:{country}:{order_by}"
        player_ids = await self.redis.zrevrange(redis_key, offset, offset + limit - 1)
        players = []
        for player_id in player_ids:
            player = await self.from_uid(int(player_id))
            if player:
                players.append(player)
        return players

    async def get_leaderboard_count(self, order_by: str = "pp", country: str | None = None) -> int:
        redis_key = f"main:leaderboard:{order_by}"
        if country:
            redis_key = f"main:leaderboard:{country}:{order_by}"
        return await self.redis.zcard(redis_key)

    async def get_countries_list(self) -> list:

        # countries = await glob.db.fetchall(
        #     "SELECT DISTINCT country FROM users WHERE country IS NOT NULL ORDER BY country"
        # )
        # return [row["country"] for row in countries] if countries else []

        stmt = select(PlayerSchema.country).distinct()
        countries_list = await self.session.execute(stmt)
        return countries_list.scalars().all()