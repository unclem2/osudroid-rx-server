import hashlib

from argon2 import PasswordHasher

from objects.models.player import PlayerModel
from objects.models.stats import StatsModel
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository


class PlayerService:  # noqa: PLR0904
    def __init__(self, player_repository: PlayerRepository, leaderboard_repository: LeaderboardRepository, player_storage: PlayerStorage, score_repository: ScoreRepository):
        self.player_repository = player_repository
        self.leaderboard_repository = leaderboard_repository
        self.player_storage = player_storage
        self.score_repository = score_repository

    async def from_uid(self, player_id: int) -> PlayerModel | None:
        model = await self.player_repository.from_uid(player_id)
        if model:
            model.pp_rank, model.score_rank, model.pp_country_rank, model.score_country_rank = await self.leaderboard_repository.get_leaderboard_placement(model)
            model.stats.level = await self.player_storage.get_level(model.id)
            model.playing = await self.player_storage.get_playing(model.id)

        return model

    async def from_username(self, username: str) -> PlayerModel | None:
        model = await self.player_repository.from_username(username)
        if model:
            model.pp_rank, model.score_rank, model.pp_country_rank, model.score_country_rank = await self.leaderboard_repository.get_leaderboard_placement(model)
            model.stats.level = await self.player_storage.get_level(model.id)
            model.playing = await self.player_storage.get_playing(model.id)

        return model

    async def update_stats(self, player: PlayerModel) -> None:
        all_scores = await self.score_repository.player_scores(player.id, "all", "date", -1)
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

        def level_formula(i):
            try:
                if i >= 100:
                    return 26931190827 + 99999999999 * (i - 100)
                return int((5000 / 3 * (4 * i**3 - 3 * i**2 - i)) + 1.25 ** (i - 60))
            except ZeroDivisionError:
                return 0

        level = 0
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
        stats.id = player.id or 0
        player.stats = stats

        await self.player_repository.update_player(player)
        await self.leaderboard_repository.set_leaderboard_placement(player)
        await self.player_storage.set_level(player)


    async def get_playing(self, player_id: int) -> str | None:
        return await self.player_storage.get_playing(player_id)

    async def set_playing(self, player_id: int, md5: str) -> None:
        await self.player_storage.set_playing(player_id, md5)

    async def get_last_online(self, player_id: int) -> float | None:
        return await self.player_storage.get_last_online(player_id)

    async def set_last_online(self, player_id: int, timestamp: float) -> None:
        await self.player_storage.set_last_online(player_id, timestamp)

    async def get_uuid(self, player_id: int) -> str | None:
        return await self.player_storage.get_uuid(player_id)

    async def get_leaderboard(self, order_by: str = "pp", country: str | None = None, limit: int = 100, offset: int = 0) -> list[PlayerModel]:
        player_ids = await self.leaderboard_repository.get_leaderboard(order_by, country, limit, offset)
        players = []
        for pid in player_ids:
            player = await self.from_uid(int(pid))
            if player:
                players.append(player)
        return players

    async def get_online_players_count(self) -> int:
        return await self.player_storage.get_online_player_count()

    async def get_player_count(self) -> int:
        return await self.leaderboard_repository.get_player_count()

    async def get_leaderboard_count(self, order_by: str = "pp", country: str | None = None) -> int:
        return await self.leaderboard_repository.get_leaderboard_count(order_by, country)

    async def get_countries_list(self) -> list:
        return await self.leaderboard_repository.get_countries_list()

    async def set_uuid(self, player_id: int, uuid: str) -> None:
        await self.player_storage.set_uuid(player_id, uuid)

    async def get_status(self, player_id: int) -> int | None:
        return await self.player_repository.get_status(player_id)

    async def set_country(self, player_id: int, country: str) -> None:
        await self.player_repository.set_country(player_id, country)

    async def new(self, username: str, password: str, device_id: str, email: str) -> PlayerModel:
        new_password_salted = password + "taikotaiko"
        new_password_hashed = hashlib.md5(new_password_salted.encode("utf-8")).hexdigest()
        new_password_crypted = PasswordHasher().hash(new_password_hashed)
        email_hash = hashlib.md5(email.encode()).hexdigest()

        player = await self.player_repository.new(username, new_password_crypted, device_id, email_hash)
        await self.player_repository.create_stats(player.id)
        await self.player_storage.set_level(player)
        return player

    async def change_email(self, player_id: int, new_email: str) -> None:
        email_hash = hashlib.md5(new_email.encode()).hexdigest()
        await self.player_repository.set_email_hash(player_id, email_hash)

    async def check_password(self, player_id: int, password: str | None, hashed_password: str | None) -> bool:
        if hashed_password is None:
            hashed_password = hashlib.md5(f"{password}taikotaiko".encode()).hexdigest()
        password_crypted = await self.player_repository.get_password(player_id)
        try:
            return PasswordHasher().verify(password_crypted, hashed_password)
        except Exception:
            return False

    async def set_password(self, player_id: int, new_password: str) -> None:
        new_password_salted = new_password + "taikotaiko"
        new_password_hashed = hashlib.md5(new_password_salted.encode("utf-8")).hexdigest()
        new_password_crypted = PasswordHasher().hash(new_password_hashed)

        await self.player_repository.set_password(player_id, new_password_crypted)

    async def change_username(self, player_id: int, new_username: str) -> None:
        model = await self.player_repository.change_username(player_id, new_username)
        await self.player_storage.set_player(model)
        
    async def init_players(self):
        players = await self.player_repository.get_everyone()
        for player in players:
            await self.update_stats(player)

    