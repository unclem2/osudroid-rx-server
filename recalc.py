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
    await pp.recalc_scores()

async def main():
    await recalc()

if __name__ == "__main__":
    asyncio.run(main())