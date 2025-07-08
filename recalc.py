import asyncio
from objects import glob
from objects.db import PostgresDB
from objects.player import Player
from objects.score import Score
from utils.pp import PPCalculator
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

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
        scores = await glob.db.fetchall(
            "SELECT * FROM scores WHERE playerid = $1", [player.id]
        )
        print(f"{player.id} - {len(scores)} scores found")

        grouped_scores = {}
        for score in scores:
            grouped_scores.setdefault(score["maphash"], []).append(score)

        for maphash, user_map_scores in grouped_scores.items():
            print(f"{player.id} - processing map {maphash}")

            for user_map_score in user_map_scores:
                try:
                    s = await Score.from_sql(user_map_score["id"])
                    print(f"{player.id} - loaded score {user_map_score['id']}")
                except Exception as e:
                    print(f"{player.id} - failed to load score {user_map_score['id']}")
                    if user_map_score["status"] is None:
                        user_map_score["status"] = 1
                        s = Score()
                        s.id = user_map_score["id"]
                        
                        s.h300 = user_map_score["hit300"]
                        s.h100 = user_map_score["hit100"]
                        s.h50 = user_map_score["hit50"]
                        s.hmiss = user_map_score["hitmiss"]
                        s.max_combo = user_map_score["combo"]
                        s.mods = user_map_score["mods"]
                        s.player = player
                        s.pp = await PPCalculator.from_score(s)
                if s.pp == False:
                    print(f"{player.id} - failed to load map {maphash}")
                    continue
                await s.pp.calc()
                user_map_score["pp"] = s.pp.calc_pp
                print(
                    f"{player.id} - calculated pp for score {user_map_score['id']} - {s.pp.calc_pp}"
                )

                await glob.db.execute(
                    "UPDATE scores SET pp = $1 WHERE id = $2", [s.pp.calc_pp, s.id]
                )
                print(f"{player.id} - updated pp for score {user_map_score['id']}")

            user_map_scores.sort(key=lambda x: x["pp"], reverse=True)

            for i, user_map_score in enumerate(user_map_scores):
                new_status = 2 if i == 0 else 1
                await glob.db.execute(
                    "UPDATE scores SET status = $1 WHERE id = $2",
                    [new_status, user_map_score["id"]],
                )
                print(
                    f"{player.id} - updated status for score {user_map_score['id']} to {new_status}"
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
