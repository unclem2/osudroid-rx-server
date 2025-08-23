import asyncio
from objects import glob
from objects.db import PostgresDB
from objects.player import Player
from objects.score import Score
from objects.beatmap import Beatmap
from utils.pp import PPCalculator
import logging

# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

glob.db = PostgresDB()

async def recalc_stats():
    players = await glob.db.fetchall("SELECT id FROM users")
    for player in players:
        player_obj = Player(id=int(player["id"]))
        await player_obj.update_stats()


async def recalc_scores():
    """never use this unless something is messed up/testing"""
    print("Recalculating scores...")

    for player in glob.players:
        print(f"{player.id} - processing")
        total_recalculated = 0
        scores = await glob.db.fetchall(
            "SELECT * FROM scores WHERE playerid = $1", [player.id]
        )
        left = len(scores)
        print(f"{player.id} - {len(scores)} scores found")

        grouped_scores = {}
        for score in scores:
            grouped_scores.setdefault(score["md5"], []).append(score)

        for md5, user_map_scores in grouped_scores.items():
            print(f"[{total_recalculated}/{left}]{player.id} - processing map {md5}")

            for score_data in user_map_scores:
                s = Score()
                
                s.id = score_data["id"]
                if s.id == 11002:
                    pass
                s.bmap = await Beatmap.from_md5(md5)
                s.md5 = md5
                s.player = player
                s.h300 = score_data["hit300"]
                s.h100 = score_data["hit100"]
                s.h50 = score_data["hit50"]
                s.hmiss = score_data["hitmiss"]
                s.max_combo = score_data["combo"]
                s.mods = score_data["mods"]
                s.pp = await PPCalculator.from_score(s)
                if s.pp != False:
                    await s.pp.calc()
                    score_data["pp"] = s.pp.calc_pp
                else:
                    score_data["pp"] = 0

                await glob.db.execute(
                    "UPDATE scores SET pp = $1 WHERE id = $2",
                    [score_data["pp"], s.id],
                )

                total_recalculated += 1  
                print(
                    f"[{total_recalculated}/{left}]{player.id} - recalculated score {s.id} with pp {score_data['pp']}"
                )

            user_map_scores.sort(key=lambda x: x["pp"], reverse=True)
            for i, user_map_score in enumerate(user_map_scores):
                new_status = 2 if i == 0 else 1
                await glob.db.execute(
                    "UPDATE scores SET status = $1 WHERE id = $2",
                    [new_status, user_map_score["id"]],
                )
                print(
                    f"[{total_recalculated}/{left}]{player.id} - updated status for score {user_map_score['id']} to {new_status}"
                )

        await player.update_stats()
        print(f"{player.id} - updated stats")




async def init_players():
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    for player_id in player_ids:
        player = await Player.from_sql(player_id["id"])
        glob.players.add(player)


async def recalc():
    await glob.db.connect()
    await init_players()
    await recalc_scores()
    await recalc_stats()


async def main():
    await recalc()


if __name__ == "__main__":
    asyncio.run(main())
