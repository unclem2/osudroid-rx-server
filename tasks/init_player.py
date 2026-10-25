from collections.abc import Callable

from objects.db import sessionmaker
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository
from objects.services.player import PlayerService


async def init_players(app_instance) -> None:
    """Initializes players by fetching their data from the database and updating their stats.
    """
    async with sessionmaker() as session:
        player_repository = PlayerRepository(session, app_instance.state.redis)
        score_repository = ScoreRepository(session, app_instance.state.redis)
        lb_repository = LeaderboardRepository(session, app_instance.state.redis)
        player_storage = PlayerStorage(session, app_instance.state.redis)
        player_service = PlayerService(player_repository, lb_repository, player_storage, score_repository)
        await player_service.init_players()


async def compose(app_instance) -> tuple[Callable, any]:
    return init_players, app_instance
