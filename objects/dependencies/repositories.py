from fastapi import Depends

from objects.dependencies.clients import get_redis
from objects.dependencies.db import get_db_session
from objects.repositories.beatmap import BeatmapRepository
from objects.repositories.leaderboard import LeaderboardRepository
from objects.repositories.player import PlayerRepository
from objects.repositories.player_storage import PlayerStorage
from objects.repositories.score import ScoreRepository


async def get_beatmap_repository(session=Depends(get_db_session), redis=Depends(get_redis)) -> BeatmapRepository:
    return BeatmapRepository(session=session, redis=redis)


async def get_player_repository(session=Depends(get_db_session), redis=Depends(get_redis)) -> PlayerRepository:
    return PlayerRepository(session=session, redis=redis)


async def get_leaderboard_repository(session=Depends(get_db_session), redis=Depends(get_redis)) -> LeaderboardRepository:
    return LeaderboardRepository(session=session, redis=redis)


async def get_player_storage(session=Depends(get_db_session), redis=Depends(get_redis)) -> PlayerStorage:
    return PlayerStorage(session=session, redis=redis)


async def get_score_repository(session=Depends(get_db_session), redis=Depends(get_redis)) -> ScoreRepository:
    return ScoreRepository(session=session, redis=redis)
