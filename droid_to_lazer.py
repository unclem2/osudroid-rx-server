from objects.mods import Mods
from objects import glob
import asyncio
from objects.db import PostgresDB
from objects.player import Player
from objects.score import Score
from objects.beatmap import Beatmap
from utils.pp import PPCalculator
import logging
import json

glob.db = PostgresDB()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def convert_db():
    await glob.db.connect()
    scores = await glob.db.fetchall("SELECT * FROM scores")
    for i, score in enumerate(scores):
        mods = score["mods"]
        if not mods:
            continue

        old_mods = Mods(mods)
        converted_mods = old_mods.convert_droid
        string = json.dumps(converted_mods, ensure_ascii=False)
        await glob.db.execute(
            "UPDATE scores SET mods = $1 WHERE id = $2",
            [string, score["id"]]
        )
        logging.info(f"[{i}/{len(scores)}]Converted mods for score ID {score['id']} from {mods} to {converted_mods}")


asyncio.run(convert_db())