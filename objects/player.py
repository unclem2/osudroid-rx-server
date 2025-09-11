import logging
import time
from dataclasses import dataclass
from objects import glob
import utils
from typing import List


@dataclass
class Stats:
    """
    Dataclass representing player statistics.
    """
    id: int
    pp_rank: int
    score_rank: int
    tscore: int
    rscore: int
    acc: float
    plays: int
    pp: float
    country_pp_rank: int
    country_score_rank: int
    playing: str = None
    @property
    def droid_acc(self) -> (int | float):
        """
        Returns the accuracy in a format suitable for client.
        For pre-1.8 state, it returns accuracy as an integer multiplied by 1000.
        For 1.8 and later, it returns accuracy as a float divided by 100 in the range of 0.00 to 1.00
        """
        return (
            int(self.acc * 1000)
            if glob.config.legacy == True
            else float(self.acc / 100)
        )

    @property
    def droid_submit_stats(self) -> str:
        """
        Returns dummy stats string for client submission.\n
        For pre-1.8 state, it returns {global rank} {pp or score} {droid_acc} {lb placement which is 0 here}.\n
        For 1.8 and later, it returns {global rank} {score} {droid_acc} {lb placement which is 0 here} {pp}.
        """
        rank = self.pp_rank if glob.config.pp else self.score_rank
        metric = self.pp if glob.config.pp and glob.config.legacy else self.rscore
        string = f"{rank} {metric} {self.droid_acc} 0"
        if not glob.config.legacy:
            string += f" {self.pp if glob.config.pp else 0}"
        return string

    @property
    def as_json(self) -> dict:
        """
        Returns the stats as a JSON serializable dictionary.
        """
        return {
            "id": self.id,
            "pp_rank": self.pp_rank,
            "score_rank": self.score_rank,
            "country_pp_rank": self.country_pp_rank,
            "country_score_rank": self.country_score_rank,
            "tscore": self.tscore,
            "rscore": self.rscore,
            "acc": self.acc,
            "plays": self.plays,
            "pp": self.pp,
            "playing": self.playing,
        }


class Player:
    """
    Class representing a player in the game.
    Attributes:
        id (str): Unique identifier for the player.
        prefix (str): Prefix for the player's name.
        username (str): Username of the player.
        username_safe (str): Safe version of the username.
        email_hash (str): MD5 hash of the player's email.
        uuid (str): Unique UUID for the player.
        last_online (float): Timestamp of the last time the player was online.
        stats (Stats): Player's statistics.
        country (str): Country of the player.
    """
    def __init__(self, **kwargs):
  
        self.id: str = kwargs.get("id")
        self.prefix: str = kwargs.get("prefix", "")
        self.username: str = kwargs.get("username")
        self.username_safe: str = utils.make_safe(self.username) if self.username else None
        self.email_hash: str = kwargs.get("email_hash", "0")
        self.uuid: str = kwargs.get("uuid", None)
        self.last_online: float = 0
        self.stats: Stats = None
        self.country: str = kwargs.get("country", None)

    def __repr__(self) -> str:
        """
        Returns a string representation of the Player object.
        """
        return f"<{self.id} - {self.username}>"

    @property
    def online(self) -> bool:
        """ 
        Checks if the player is online based on the last_online timestamp.
        Returns:
            bool: True if the player is online, False otherwise.
        """
        return time.time() - 150 < self.last_online

    @property
    def as_json(self) -> dict:
        """ 
        Returns the player data as a JSON serializable dictionary.
        """
        return {
            "id": self.id,
            "country": self.country,
            "prefix": self.prefix,
            "username": self.username,
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
        top_scores = await glob.db.fetchall(
            """
            SELECT acc, pp, score
            FROM scores s
            WHERE s.playerID = $1
                AND s.status = 2
                AND s.md5 IN (SELECT md5 FROM maps WHERE status IN (1, 2, 4, 5))
            ORDER BY s.pp DESC
        """,
            [int(self.id)],
        )

        # Fetch all scores (total plays)
        all_scores = await glob.db.fetchall(
            "SELECT acc, pp, score FROM scores WHERE playerID = $1", [int(self.id)]
        )


        if not top_scores or not all_scores:
            logging.error(
                f"Failed to find player scores when updating stats. (Ignore if the player is new, id: {self.id})"
            )
            return

        stats = self.stats or Stats(
            id=int(self.id),
            pp_rank=0,
            score_rank=0,
            tscore=0,
            rscore=0,
            acc=100,
            plays=0,
            pp=0,
            country_pp_rank=0,
            country_score_rank=0,
            playing="",
        )

        # Average accuracy from top scores
        stats.acc = sum(row["acc"] for row in top_scores) / len(top_scores)

        # Weighted pp calculation (top 100 scores)
        total_pp = 0
        for i, row in enumerate(top_scores[:100]):
            weight = 0.95**i
            weighted_pp = row["pp"] * weight
            total_pp += weighted_pp
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

        country_pp_rank_result = await glob.db.fetch(
            """
            SELECT COUNT(*) AS c
            FROM stats s
            INNER JOIN users u ON u.id = s.id
            WHERE u.country = $1 AND s.pp > $2
            """,
            [self.country, int(stats.pp)],
        )
        country_score_rank_result = await glob.db.fetch(
            """
            SELECT COUNT(*) AS c
            FROM stats s
            INNER JOIN users u ON u.id = s.id
            WHERE u.country = $1 AND s.rscore > $2
            """,
            [self.country, int(stats.rscore)],
        )
        stats.country_pp_rank = country_pp_rank_result["c"] + 1
        stats.country_score_rank = country_score_rank_result["c"] + 1

        # Update database
        await glob.db.execute(
            """
            UPDATE stats
            SET acc = $1, pp_rank = $2, pp = $3, rscore = $4, tscore = $5, plays = $6,
                score_rank = $7, country_pp_rank = $8, country_score_rank = $9
            WHERE id = $10
        """,
            [
                stats.acc,
                stats.pp_rank,
                stats.pp,
                stats.rscore,
                stats.tscore,
                stats.plays,
                stats.score_rank,
                stats.country_pp_rank,
                stats.country_score_rank,
                self.id,
            ],
        )

    async def get_scores(self, limit: int = -1) -> List["Score"] | None:
        """
        Fetches the player's scores from the database.
        Args:
            limit (int): The maximum number of scores to fetch. Default is -1 (no limit).
        Returns:
            List[Score]: A list of Score objects representing the player's scores.
        """
        from objects.score import Score
        query = "SELECT * FROM scores WHERE playerid = $1 ORDER BY id DESC"
        if limit != -1:
            query += f" LIMIT {limit}"
        scores_data = await glob.db.fetchall(query, [int(self.id)])
        scores = []
        for row in scores_data:
            scores.append(await Score.from_sql(0, res=row))
        return scores
    
    async def top_scores(self, limit: int = -1) -> List["Score"] | None:
        """
        Fetches the player's top scores from the database.
        Args:
            limit (int): The maximum number of scores to fetch. Default is -1 (no limit).
        Returns:
            List[Score]: A list of Score objects representing the player's top scores.
        """
        from objects.score import Score
        query = """
            SELECT *
            FROM scores s
            WHERE s.playerID = $1
                AND s.status = 2
                AND s.md5 IN (SELECT md5 FROM maps WHERE status IN (1, 2, 4, 5))
            ORDER BY s.pp DESC
        """
        if limit != -1:
            query += f" LIMIT {limit}"
        scores_data = await glob.db.fetchall(query, [int(self.id)])
        scores = []
        for row in scores_data:
            scores.append(await Score.from_sql(0, res=row))

        return scores

