import asyncio
from objects import glob, score
from objects.db import PostgresDB
from utils import pp
from objects.player import Player

from objects.player import recalc_stats

glob.db = PostgresDB()


async def init_players():
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    for player_id in player_ids:
        player = await Player.from_sql(player_id["id"])
        glob.players.add(player)

async def recalc():
    await glob.db.connect()
    await init_players()
    # await insert_whitelist()
    await score.recalc_scores()
    # await pp.recalc_single_score(13061)
    await recalc_stats()


async def main():
    await recalc()


if __name__ == "__main__":
    asyncio.run(main())
