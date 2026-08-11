from osudroid_api_wrapper.classes.base.player import Player
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from objects.models.player import PlayerModel
from objects.schemas.player import PlayerSchema


class PlayerStorage:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    async def set_player(self, player: PlayerModel) -> None:
        await self.redis.set(f"main:player:{player.id}:data", player.model_dump_json(exclude={"pp_rank", "pp_country_rank", "score_rank", "score_country_rank", "playing"}))

    async def get_player(self, player_id: int) -> PlayerModel | None:
        player = await self.redis.get(f"main:player:{player_id}:data")
        return PlayerModel.model_validate_json(player) if player else None

    async def set_level(self, player: PlayerModel) -> None:
        await self.redis.set(f"main:player:{player.id}:level", player.stats.level)

    async def get_level(self, player_id: int) -> int | None:
        level = await self.redis.get(f"main:player:{player_id}:level")
        return int(level) if level else None

    async def set_playing(self, player_id: int, md5: str) -> None:
        await self.redis.setex(f"main:player:{player_id}:playing", 600, md5)

    async def get_playing(self, player_id: int) -> str | None:
        playing = await self.redis.get(f"main:player:{player_id}:playing")
        if isinstance(playing, bytes):
            return playing.decode()
        return playing or None

    async def set_uuid(self, player_id: int, uuid: str) -> None:
        await self.redis.set(f"main:player:{player_id}:uuid", uuid)

    async def get_uuid(self, player_id: int) -> str | None:
        uuid = await self.redis.get(f"main:player:{player_id}:uuid")
        if isinstance(uuid, bytes):
            return uuid.decode()
        return uuid or None

    async def set_last_online(self, player_id: int, timestamp: float) -> None:
        await self.redis.setex(f"main:player:{player_id}:last_online", 600, str(timestamp))

    async def get_last_online(self, player_id: int) -> float | None:
        last_online = await self.redis.get(f"main:player:{player_id}:last_online")
        return float(last_online) if last_online else None

    async def get_online_player_count(self) -> int:
        count = 0
        async for _ in self.redis.scan_iter("main:player:*:playing"):
            count += 1
        return count
