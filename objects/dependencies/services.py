from fastapi import Depends

from objects.dependencies.clients import get_osu_api_client, get_processor, get_redis
from objects.dependencies.config import get_config
from objects.dependencies.repositories import (
    get_beatmap_repository,
    get_leaderboard_repository,
    get_player_repository,
    get_player_storage,
    get_score_repository,
)
from objects.services.beatmap import BeatmapService
from objects.services.player import PlayerService
from objects.services.recalc import RecalcService
from objects.services.score import ScoreService


def get_beatmap_service(repository=Depends(get_beatmap_repository), config=Depends(get_config), processor_client=Depends(get_processor), osu_api_client=Depends(get_osu_api_client)) -> BeatmapService:
    return BeatmapService(
        repository=repository,
        config=config,
        processor_client=processor_client,
        osu_api_client=osu_api_client,
    )


def get_player_service(player_repository=Depends(get_player_repository), leaderboard_repository=Depends(get_leaderboard_repository), player_storage=Depends(get_player_storage), score_repository=Depends(get_score_repository)) -> PlayerService:
    return PlayerService(
        player_repository=player_repository,
        leaderboard_repository=leaderboard_repository,
        player_storage=player_storage,
        score_repository=score_repository,
    )


def get_score_service(score_repository=Depends(get_score_repository), player_service=Depends(get_player_service), beatmap_service=Depends(get_beatmap_service), processor_client=Depends(get_processor)) -> ScoreService:
    return ScoreService(
        score_repository=score_repository,
        player_service=player_service,
        beatmap_service=beatmap_service,
        processor_client=processor_client,
    )


def get_recalc_service(config=Depends(get_config), processor_client=Depends(get_processor), osu_api_client=Depends(get_osu_api_client), redis=Depends(get_redis)) -> RecalcService:
    return RecalcService(
        processor_client=processor_client,
        config=config,
        osu_api_client=osu_api_client,
        redis=redis,
    )
