from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from objects.models.player import PlayerModel
from objects.schemas.player import PlayerSchema
from objects.schemas.stats import StatsSchema


class PlayerRepository:
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
        player = await self.session.get(PlayerSchema, player_id)
        model = self._serizalize(player) if player else None

        return model

    async def from_username(self, username: str) -> PlayerModel | None:
        player_query = await self.session.execute(select(PlayerSchema).where(PlayerSchema.username == username))
        player = player_query.scalar_one_or_none()
        model = self._serizalize(player) if player else None

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

        return model

    async def update_player(self, player: PlayerModel) -> None:
        player_schema = self._deserialize(player)
        await self.session.merge(player_schema)
        await self.session.commit()

    async def set_password(self, player_id: int, new_password_hash: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.password_hash = new_password_hash
            await self.session.commit()

    async def get_password(self, player_id: int) -> str | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.password_hash if player else None

    async def set_country(self, player_id: int, country: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.country = country
            await self.session.commit()

    async def set_status(self, player_id: int, status: int) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.status = status
            await self.session.commit()

    async def get_status(self, player_id: int) -> int | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.status if player else None

    async def change_username(self, player_id: int, new_username: str) -> PlayerModel | None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.username = new_username
            await self.session.commit()
            return self._serizalize(player)
        return None

    async def set_email_hash(self, player_id: int, email_hash: str) -> None:
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.email_hash = email_hash
            await self.session.commit()

    async def get_email_hash(self, player_id: int) -> str | None:
        player = await self.session.get(PlayerSchema, player_id)
        return player.email_hash if player else None

    async def create_stats(self, player_id: int) -> None:
        stats = StatsSchema(id=player_id, pp=0, accuracy=100, playcount=0, total_score=0, ranked_score=0)
        self.session.add(stats)
        await self.session.commit()

    async def get_everyone(self) -> list[PlayerModel]:
        response = await self.session.execute(select(PlayerSchema))
        players = response.scalars().all()

        return [self._serizalize(player) for player in players]

    async def set_device_id(self, player_id, device_id: str):
        player = await self.session.get(PlayerSchema, player_id)
        if player:
            player.device_id = device_id
            await self.session.commit()

    async def get_device_id(self, player_id: int):
        player = await self.session.get(PlayerSchema, player_id)
        return player.device_id if player else None
    