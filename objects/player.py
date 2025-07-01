import logging
import time
from dataclasses import dataclass
from objects import glob
import utils


@dataclass
class Stats:
    id: int
    pp_rank: int 
    score_rank: int 
    tscore: int 
    rscore: int 
    acc: float 
    plays: int 
    pp: float 
    playing: str = None

    @property
    def droid_acc(self):
        return (
            int(self.acc * 1000)
            if glob.config.legacy == True
            else float(self.acc / 100)
        )

    @property
    def droid_submit_stats(self):
        string = f"{self.pp_rank if glob.config.pp else self.score_rank} "
        if glob.config.legacy == True:
            string += f"{self.pp if glob.config.pp else self.rscore} "
        else:
            string += f"{self.rscore} "
        string += f"{self.droid_acc} 0"
        if glob.config.legacy == False:
            if glob.config.pp:
                string += f" {self.pp}"
            else:
                string += f" 0"
                
        return string

    @property
    def as_json(self):
        return {
            "id": self.id,
            "pp_rank": self.pp_rank,
            "score_rank": self.score_rank,
            "total_score": self.tscore,
            "ranked_score": self.rscore,
            "accuracy": self.acc,
            "plays": self.plays,
            "pp": self.pp,
            "is_playing": self.playing,
        }


class Player:
    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id")
        self.prefix: str = kwargs.get("prefix", "")
        self.name: str = kwargs.get("username")
        self.name_safe: str = utils.make_safe(self.name) if self.name else None

        #
        self.email_hash: str = kwargs.get(
            "email_hash", "35da3c1a5130111d0e3a5f353389b476"
        )  # used for gravatar, default to my pfp lole
        self.uuid: str = kwargs.get("uuid", None)  # ...yea

        self.last_online: float = 0
        self.stats: Stats = None
        self.country: str = kwargs.get("country", None)

    def __repr__(self):
        return f"<{self.id} - {self.name}>"

    @property
    def online(self):
        # 30 seconds timeout, not really accurate cuz we update the last_online time on login and submit
        return time.time() - 150 < self.last_online

    @property
    def as_json(self):
        return {
            "id": self.id,
            "country": self.country,
            "prefix": self.prefix,
            "name": self.name,
            "online": self.online,
            "stats": self.stats.as_json,
        }

    @classmethod
    async def from_sql(cls, user_id: int):
        user_data = await glob.db.fetch(
            "SELECT id, prefix, username, email_hash, email, country FROM users WHERE id = $1",
            [int(user_id)],
        )
        user_stats = await glob.db.fetch(
            "SELECT * FROM stats WHERE id = $1", [int(user_id)]
        )
        if not user_data or not user_stats:
            raise Exception("Failed to get user from database.")

        # fix email_hash if its none and user got email (there should be)
        if user_data["email_hash"] is None and user_data["email"] is not None:
            email_hash = utils.make_md5(user_data["email"])
            await glob.db.execute(
                "UPDATE users SET email_hash = ? WHERE id = ?", [email_hash, user_id]
            )

        user_data.pop("email", None)

        p = cls(**user_data)
        p.stats = Stats(**user_stats)

        return p

    async def update_stats(self):
        # Fetch player scores
        top_scores = await glob.db.fetchall("""
        SELECT * 
        FROM scores s
        WHERE s.playerID = $1 
            AND s.status = 2 
            AND s.maphash IN (SELECT md5 FROM maps WHERE status IN (1, 2, 4, 5))
        ORDER BY s.pp 
        DESC
        """, [int(self.id)]
        )

        all_scores = await glob.db.fetchall(
            """
            SELECT * 
            FROM scores 
            WHERE playerID = $1
            """, [int(self.id)]
        )

        if not top_scores or not all_scores:
            logging.error(
                f"Failed to find player scores when updating stats. (Ignore if the player is new, id: {self.id})"
            )
            return
        try:
            stats = self.stats
        except:
            stats = Stats(
                id=self.id, rank=0, tscore=0, rscore=0, acc=100, plays=0, pp=0
            ) 

        # Calculate average accuracy
        if stats is None:
            stats = Stats(
                id=self.id, rank=0, tscore=0, rscore=0, acc=100, plays=0, pp=0
            )   
        stats.acc = sum(row["acc"] for row in top_scores) / len(top_scores)

        # Calculate performance points (pp)
        total_pp = 0
        for i, row in enumerate(top_scores[:100]):
            weight = 0.95**i
            weighted_pp = row["pp"] * weight
            total_pp += weighted_pp
            logging.debug(f'Score: {row["pp"]}, Weight: {weight}, Weighted PP: {weighted_pp}')
        stats.pp = round(total_pp)
        stats.rscore = sum(row["score"] for row in top_scores)
        stats.tscore = sum(row["score"] for row in all_scores)

        score_rank_query = """
        SELECT COUNT(*) AS c 
        FROM stats 
        WHERE rscore > $1
        
        """
        score_rank_result = await glob.db.fetch(
            score_rank_query, [int(stats.rscore)]
        )

        pp_rank_query = """ 
        SELECT COUNT(*) AS c
        FROM stats 
        WHERE pp > $1
        """
        pp_rank_result = await glob.db.fetch(
            pp_rank_query, [int(stats.pp)]
        )
        stats.score_rank = score_rank_result["c"] + 1
        stats.pp_rank = pp_rank_result["c"] + 1
        stats.plays = len(all_scores)

        # Update stats in the database
        update_query = "UPDATE stats SET acc = $1, pp_rank = $2, pp = $3, rscore = $4, tscore = $5, plays = $6, score_rank = $7 WHERE id = $8"
        await glob.db.execute(
            update_query,
            [
                stats.acc,
                stats.pp_rank,
                stats.pp,
                stats.rscore,
                stats.tscore,
                stats.plays,
                stats.score_rank,
                self.id
            ],
        )


async def recalc_stats():
    # Fetch players from the database
    players = await glob.db.fetchall("SELECT id FROM users")

    for player in players:
        # Assuming you have a Player class that can update stats
        player_obj = Player(id=int(player["id"]))
        await player_obj.update_stats()
