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
    country_pp_rank: int = 0
    country_score_rank: int = 0
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
            "country_pp_rank": self.country_pp_rank,
            "country_score_rank": self.country_score_rank,
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
        self.email_hash: str = kwargs.get("email_hash", "35da3c1a5130111d0e3a5f353389b476")
        self.uuid: str = kwargs.get("uuid", None)
        self.last_online: float = 0
        self.stats: Stats = None
        self.country: str = kwargs.get("country", None)

    def __repr__(self):
        return f"<{self.id} - {self.name}>"

    @property
    def online(self):
        # 30 seconds timeout (actually 150 here)
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

        # Fix missing email_hash if needed
        if user_data["email_hash"] is None and user_data["email"] is not None:
            email_hash = utils.make_md5(user_data["email"])
            await glob.db.execute(
                "UPDATE users SET email_hash = ? WHERE id = ?", [email_hash, user_id]
            )
            user_data["email_hash"] = email_hash

        user_data.pop("email", None)

        p = cls(**user_data)
        p.stats = Stats(**user_stats)
        return p

    async def update_stats(self):
        # Fetch top ranked scores (status=2 and approved maps)
        top_scores = await glob.db.fetchall("""
            SELECT *
            FROM scores s
            WHERE s.playerID = $1
                AND s.status = 2
                AND s.maphash IN (SELECT md5 FROM maps WHERE status IN (1, 2, 4, 5))
            ORDER BY s.pp DESC
        """, [int(self.id)])

        # Fetch all scores (total plays)
        all_scores = await glob.db.fetchall(
            "SELECT * FROM scores WHERE playerID = $1", [int(self.id)]
        )

        if not top_scores or not all_scores:
            logging.error(
                f"Failed to find player scores when updating stats. (Ignore if the player is new, id: {self.id})"
            )
            return

        stats = self.stats or Stats(
            id=int(self.id), pp_rank=0, score_rank=0, tscore=0, rscore=0, acc=100, plays=0, pp=0
        )

        # Average accuracy from top scores
        stats.acc = sum(row["acc"] for row in top_scores) / len(top_scores)

        # Weighted pp calculation (top 100 scores)
        total_pp = 0
        for i, row in enumerate(top_scores[:100]):
            weight = 0.95 ** i
            weighted_pp = row["pp"] * weight
            total_pp += weighted_pp
            logging.debug(f'Score: {row["pp"]}, Weight: {weight}, Weighted PP: {weighted_pp}')
        stats.pp = round(total_pp)

        stats.rscore = sum(row["score"] for row in top_scores)
        stats.tscore = sum(row["score"] for row in all_scores)
        stats.plays = len(all_scores)

        # Global ranks
        pp_rank_result = await glob.db.fetch(
            "SELECT COUNT(*) AS c FROM stats WHERE pp > $1", [int(stats.pp)]
        )
        score_rank_result = await glob.db.fetch(
            "SELECT COUNT(*) AS c FROM stats WHERE rscore > $1", [int(stats.rscore)]
        )
        stats.pp_rank = pp_rank_result["c"] + 1
        stats.score_rank = score_rank_result["c"] + 1

        # Country ranks (if player has country)
        if self.country:
            country_pp_rank_result = await glob.db.fetch(
                """
                SELECT COUNT(*) AS c
                FROM stats s
                INNER JOIN users u ON u.id = s.id
                WHERE u.country = $1 AND s.pp > $2
                """, [self.country, int(stats.pp)]
            )
            country_score_rank_result = await glob.db.fetch(
                """
                SELECT COUNT(*) AS c
                FROM stats s
                INNER JOIN users u ON u.id = s.id
                WHERE u.country = $1 AND s.rscore > $2
                """, [self.country, int(stats.rscore)]
            )
            stats.country_pp_rank = country_pp_rank_result["c"] + 1
            stats.country_score_rank = country_score_rank_result["c"] + 1
        else:
            stats.country_pp_rank = 0
            stats.country_score_rank = 0

        # Update database
        await glob.db.execute("""
            UPDATE stats
            SET acc = $1, pp_rank = $2, pp = $3, rscore = $4, tscore = $5, plays = $6,
                score_rank = $7, country_pp_rank = $8, country_score_rank = $9
            WHERE id = $10
        """, [
            stats.acc,
            stats.pp_rank,
            stats.pp,
            stats.rscore,
            stats.tscore,
            stats.plays,
            stats.score_rank,
            stats.country_pp_rank,
            stats.country_score_rank,
            self.id
        ])

        # update self.stats too
        self.stats = stats


async def recalc_stats():
    players = await glob.db.fetchall("SELECT id FROM users")
    for player in players:
        player_obj = Player(id=int(player["id"]))
        await player_obj.update_stats()