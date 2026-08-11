from objects.repositories.player_storage import PlayerStorage
from objects.repositories.leaderboard import LeaderboardRepository
from collections.abc import Callable

from objects.db import sessionmaker
from objects.repositories.player import PlayerRepository
from objects.repositories.score import ScoreRepository
from objects.services.player import PlayerService


async def init_players(player_service: PlayerService) -> None:
    """Initializes players by fetching their data from the database and updating their stats.
    """
    await player_service.init_players()


async def compose(app_instance) -> tuple[Callable, PlayerService]:
    session = sessionmaker()
    player_repository = PlayerRepository(session, app_instance.state.redis)
    score_repository = ScoreRepository(session, app_instance.state.redis)
    lb_repository = LeaderboardRepository(session, app_instance.state.redis)
    player_storage = PlayerStorage(session, app_instance.state.redis)
    player_service = PlayerService(player_repository, lb_repository, player_storage, score_repository)

    return init_players, player_service
