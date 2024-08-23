import os
import logging
import asyncio
import coloredlogs
from quart import Quart

# sus
from objects import glob
from objects.player import Player
from objects.db import PostgresDB

# handlers
from handlers import (cho, api)
from handlers.response import Failed

#
import utils

# testing
from utils import pp
from objects.beatmap import Beatmap



glob.db = PostgresDB()

async def recalc():
    await glob.db.connect()
    # await pp.recalc_scores()    
    await pp.recalc_stats()

async def create_stats_entries():
    query = '''
        INSERT INTO stats (id, rank, pp, acc, tscore, rscore, plays)
        VALUES ($1, 0, 0, 100.0, 0, 0, 0)
        ON CONFLICT (id) DO NOTHING;
    '''
    
    for i in range(1, 100):
        await glob.db.execute(query, [i])
            

async def main():
    # await recalc()
    await create_stats_entries()

if __name__ == "__main__":
    asyncio.run(main())