import hashlib

from argon2 import PasswordHasher

from objects.models.player import PlayerModel
from objects.models.stats import StatsModel
from objects.repositories.player import PlayerRepository
from objects.repositories.score import ScoreRepository


class PlayerService:  # noqa: PLR0904
    def __init__(self, player_repository: PlayerRepository, score_repository: ScoreRepository):
        self.player_repository = player_repository
        self.score_repository = score_repository

    async def from_uid(self, player_id: int) -> PlayerModel | None:
        return await self.player_repository.from_uid(player_id)

    async def from_username(self, username: str) -> PlayerModel | None:
        return await self.player_repository.from_username(username)

    async def new(self, username: str, password: str, device_id: str, email: str) -> PlayerModel:
        password_salted = password + "taikotaiko"
        password_hashed = hashlib.md5(password_salted.encode("utf-8")).hexdigest()
        password_crypted = PasswordHasher().hash(password_hashed)

        email_hashed = hashlib.md5(email.encode("utf-8")).hexdigest()

        username_wo_spaces = username.lower().replace(" ", "")

        return await self.player_repository.new(username_wo_spaces, password_crypted, device_id, email_hashed)

    async def check_password(self, player_id: int, password: str | None, hashed_password: str | None) -> bool:
        if hashed_password is None:
            hashed_password = hashlib.md5(f"{password}taikotaiko".encode("utf-8")).hexdigest()
        password_crypted = await self.player_repository.get_password(player_id)
        try:
            return PasswordHasher().verify(password_crypted, hashed_password)
        except:
            return False

    async def set_password(self, player_id: int, new_password: str) -> None:
        new_password_salted = new_password + "taikotaiko"
        new_password_hashed = hashlib.md5(new_password_salted.encode("utf-8")).hexdigest()
        new_password_crypted = PasswordHasher().hash(new_password_hashed)

        await self.player_repository.set_password(player_id, new_password_crypted)

    async def update_stats(self, player: PlayerModel) -> None:
        all_scores = await self.score_repository.player_scores(player.id, "best", "date", -1)
        top_scores = await self.score_repository.player_top_scores(player.id, 100)

        stats = StatsModel()
        stats.total_score = sum(score.score for score in all_scores)
        stats.ranked_score = sum(score.score for score in top_scores)
        stats.accuracy = sum(score.accuracy for score in all_scores) / len(all_scores) if all_scores else 0.0
        stats.playcount = len(all_scores)

        total_pp = 0
        for i, score in enumerate(top_scores):
            total_pp += score.pp * (0.95 ** i)
        stats.pp = total_pp

        level = 0

        
        def level_formula(i):
            try:
                if i >= 100:
                    return 26931190827 + 99999999999 * (i - 100)
                return int((5000 / 3 * (4 * i**3 - 3 * i**2 - i)) + 1.25 ** (i - 60))
            except ZeroDivisionError:
                return 0

        i = 1
        while True:
            cur = level_formula(i)
            nxt = level_formula(i + 1)
            if cur <= int(stats.ranked_score) and nxt >= int(stats.ranked_score):
                level = i
                break
            i += 1
            if cur > int(stats.ranked_score) and nxt > int(stats.ranked_score):
                level = i
                break

        stats.level = level
        stats.id = player.id if player.id else 0
        player.stats = stats

        await self.player_repository.update_player(player)
        # await self.player_repository.update_leaderboard(player)
        # await self.player_repository.update_level(player)

    async def get_status(self, player_id: int) -> int | None:
        return await self.player_repository.get_status(player_id)

    async def set_status(self, player_id: int, status: int) -> None:
        await self.player_repository.set_status(player_id, status)

    async def get_playing(self, player_id: int) -> str | None:
        return await self.player_repository.get_playing(player_id)

    async def set_playing(self, player_id: int, md5: str) -> None:
        await self.player_repository.set_playing(player_id, md5)

    async def get_last_online(self, player_id: int) -> float | None:
        return await self.player_repository.get_last_online(player_id)

    async def set_last_online(self, player_id: int, timestamp: float) -> None:
        await self.player_repository.set_last_online(player_id, timestamp)

    async def get_uuid(self, player_id: int) -> str | None:
        return await self.player_repository.get_uuid(player_id)

    async def set_uuid(self, player_id: int, uuid: str) -> None:
        await self.player_repository.set_uuid(player_id, uuid)

    async def set_country(self, player_id: int, country: str) -> None:
        await self.player_repository.set_country(player_id, country)

    async def init_players(self) -> None:
        await self.player_repository.init_players()

    async def change_username(self, player_id: int, new_username: str) -> None:
        new_username_safe = new_username.lower().replace(" ", "")
        await self.player_repository.change_username(player_id, new_username_safe)

    async def change_email(self, player_id: int, new_email: str) -> None:
        new_email_hashed = hashlib.md5(new_email.encode("utf-8")).hexdigest()
        await self.player_repository.set_email_hash(player_id, new_email_hashed)

    async def get_leaderboard(self, order_by: str = "pp", country: str | None = None, limit: int = 100, offset: int = 0) -> list[PlayerModel]:
        return await self.player_repository.get_leaderboard(order_by, country, limit, offset)

    async def get_online_players_count(self) -> int:
        return await self.player_repository.get_online_player_count()

    async def get_player_count(self) -> int:
        return await self.player_repository.get_player_count()

    async def get_leaderboard_count(self, order_by: str = "pp", country: str | None = None) -> int:
        return await self.player_repository.get_leaderboard_count(order_by, country)

    async def get_countries_list(self) -> list:
        return await self.player_repository.get_countries_list()