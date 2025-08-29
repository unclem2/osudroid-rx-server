import aiohttp
import logging
from enum import IntEnum, unique
from datetime import datetime
from pathlib import Path
from objects import glob
from typing import Optional

beatmap_folder = Path.cwd() / "data/beatmaps"


@unique
class RankedStatus(IntEnum):
    """
    Enum representing the ranked status of a beatmap.

    Attributes:
        Graveyard (int): -2 — The beatmap is in the graveyard (locally or on Bancho).
        NotSubmitted (int): -1 — The beatmap is not found (locally or on Bancho).
        Pending (int): 0 — The beatmap is pending (Bancho).
        Ranked (int): 1 — The beatmap is ranked (Bancho).
        Approved (int): 2 — The beatmap is approved (Bancho).
        Qualified (int): 3 — The beatmap is qualified (Bancho).
        Loved (int): 4 — The beatmap is loved (Bancho).
        Whitelisted (int): 5 — The beatmap is whitelisted (locally).
    """

    Graveyard = -2
    NotSubmitted = -1
    Pending = 0
    Ranked = 1
    Approved = 2
    Qualified = 3
    Loved = 4
    Whitelisted = 5

    def __str__(self):
        return self.name

class Beatmap:
    """
    Represents a beatmap object with various attributes and methods to interact with it.
    Attributes:
        id (int): Beatmap ID from bancho.
        set_id (int): Beatmapset ID from bancho.
        md5 (str): MD5 hash of the beatmap file.
        artist (str): Artist of the beatmap.
        title (str): Title of the beatmap.
        version (str): Version of the beatmap.
        creator (str): Creator of the beatmap.
        last_update (datetime): Last update time of the beatmap.
        total_length (float): Total length of the beatmap in seconds.
        max_combo (int): Maximum combo of the beatmap.
        status (RankedStatus): Map ranked status, represented by the RankedStatus enum.
        mode (int): Game mode of the beatmap.(not really used)
        bpm (float): BPM of the beatmap.
        cs (float): Circle size of the beatmap.
        od (float): Overall difficulty of the beatmap.
        ar (float): Approach rate of the beatmap.
        hp (float): Health drain of the beatmap.
        star (float): Star rating of the beatmap.
    """

    def __init__(self, **kwargs):
        self.id: int = int(
            kwargs["id"] if "id" in kwargs else kwargs.get("beatmap_id", -1)
        )
        self.set_id: int = int(
            kwargs["set_id"] if "set_id" in kwargs else kwargs.get("beatmapset_id", -1)
        )
        self.md5: str = kwargs.get("md5", "") or kwargs.get("file_md5", "")

        self.artist: str = kwargs.get("artist", "")
        self.title: str = kwargs.get("title", "")
        self.version: str = kwargs.get("version", "")
        self.creator: str = kwargs.get("creator", "")

        self.last_update: datetime = kwargs.get("last_update", 0.0)
        self.total_length: float = float(kwargs.get("total_length", 0.0))
        self.max_combo: int = int(kwargs.get("max_combo", 0))

        self.status: RankedStatus = RankedStatus(
            int(kwargs["status"] if "status" in kwargs else kwargs.get("approved", -1))
        )

        self.mode: int = int(kwargs.get("mode", 0))
        self.bpm: float = float(kwargs.get("bpm", 0.0))
        self.cs: float = float(kwargs.get("cs", 0.0) or kwargs.get("diff_size", 0.0))
        self.od: float = float(kwargs.get("od", 0.0) or kwargs.get("diff_overall", 0.0))
        self.ar: float = float(
            kwargs.get("ar", 0.0) or kwargs.get("diff_approach", 0.0)
        )
        self.hp: float = float(kwargs.get("hp", 0.0) or kwargs.get("diff_drain", 0.0))

        self.star: float = float(kwargs.get("star", 0))

    @property
    def filename(self) -> str:
        """Returns the filename of the beatmap in the format: ID.osu"""
        return f"{self.id}.osu"

    @property
    def full(self) -> str:
        """Returns the full name of the beatmap in the format: Artist - Title [Version]"""
        return f"{self.artist} - {self.title} [{self.version}]"

    @property
    def gives_reward(self) -> bool:
        """Returns True if the beatmap is ranked, approved, loved, or whitelisted"""
        return self.status in (
            RankedStatus.Ranked,
            RankedStatus.Approved,
            RankedStatus.Loved,
            RankedStatus.Whitelisted,
        )

    async def download(self) -> Optional[Path]:
        """
        Download the map using old.ppy.sh/osu/{id} and save it to the beatmap folder.
        Returns:
            Optional[Path]: The path to the downloaded beatmap file if successful, otherwise None.
        """
        # Check if the beatmap is already downloaded
        path = beatmap_folder / self.filename
        if path.exists():
            return path

        # Download the .osu file from bancho
        url = f"https://old.ppy.sh/osu/{self.id}"
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as res:
                if not res or res.status != 200:
                    return

                content = await res.read()

        # Write the content to path
        path.write_bytes(content)
        return path

    @classmethod
    async def from_md5(cls, md5: str) -> Optional["Beatmap"]:
        """
        Fetch a beatmap by its MD5 hash.
        Args:
            md5 (str): The MD5 hash of the beatmap.
        Returns:
            Optional[Beatmap]: The beatmap object if found, otherwise None.
        """

        # # Return cached beatmap if it exists
        # if beatmap := glob.cache["beatmaps"].get(md5):
        #     return beatmap

        # If the beatmap is unsubmitted, return None
        if md5 in glob.cache["unsubmitted"]:
            return

        # Try to get beatmap from database
        beatmap = await cls.from_sql(md5=md5, bid=None)

        # If not found in database, try to get it from osuapi
        if beatmap is None:
            if len(glob.config.osu_key) < 32:
                logging.info("Failed to get beatmap, invalid api key.")
                return

            if not (beatmap := await cls.from_md5_osuapi(md5)):
                glob.cache["unsubmitted"].append(md5)
                return

        # Put the beatmap in the cache
        glob.cache["beatmaps"][md5] = beatmap
        return beatmap

    @classmethod
    async def from_md5_osuapi(cls, md5: str) -> Optional["Beatmap"]:
        """
        Fetches a beatmap from the old osu! API using its MD5 hash and constructs a Beatmap instance.

        Args:
            md5 (str): The MD5 hash of the beatmap file.

        Returns:
            Optional[Beatmap]: The created Beatmap object if successful; None otherwise.
        """
        url = "https://old.ppy.sh/api/get_beatmaps"
        params = {"k": glob.config.osu_key, "h": md5}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if not data:
                    return None

        bmap = data[0]

        # Create a Beatmap instance using API response
        beatmap = cls(**bmap)
        beatmap.md5 = md5
        beatmap.last_update = datetime.strptime(
            bmap["last_update"], "%Y-%m-%d %H:%M:%S"
        )

        # Save to local SQL database
        await beatmap.save_to_sql()

        return beatmap
    
    @classmethod
    async def from_bid(cls, bid: int) -> Optional["Beatmap"]:
        """
        Fetch a beatmap by its beatmap ID (bid).
        Args:
            bid (int): The beatmap ID.
        Returns:
            Optional[Beatmap]: The beatmap object if found, otherwise None.
        """

        # # Return cached beatmap if it exists
        # for beatmap in glob.cache["beatmaps"].values():
        #     if beatmap.id == bid:
        #         return beatmap

        # Try to get beatmap from database
        beatmap = await cls.from_sql(md5=None, bid=bid)

        # If not found in database, try to get it from osuapi
        if beatmap is None:
            if len(glob.config.osu_key) < 32:
                logging.info("Failed to get beatmap, invalid api key.")
                return

            if not (beatmap := await cls.from_bid_osuapi(bid)):
                return
        # Put the beatmap in the cache
        glob.cache["beatmaps"][beatmap.md5] = beatmap
        return beatmap


    @classmethod
    async def from_bid_osuapi(cls, bid: int) -> Optional["Beatmap"]:
        """
        Fetches a beatmap from the old osu! API using its beatmap ID (bid) and constructs a Beatmap instance.

        Args:
            bid (int): The beatmap ID from osu!.

        Returns:
            Optional[Beatmap]: The created Beatmap object if successful; None otherwise.
        """
        url = "https://old.ppy.sh/api/get_beatmaps"
        params = {"k": glob.config.osu_key, "b": bid}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if not data:
                    return None

        bmap = data[0]

        # Create a Beatmap instance using API response
        beatmap = cls(**bmap)
        beatmap.last_update = datetime.strptime(
            bmap["last_update"], "%Y-%m-%d %H:%M:%S"
        )

        # Optionally save to database
        await beatmap.save_to_sql()

        return beatmap

    @property
    def as_json(self) -> dict:
        """
        Returns a dictionary representation of the beatmap object.
        This is useful for serialization or API responses.
        Returns:
            dict: A dictionary containing the beatmap's attributes.
        """
        return {
            "id": self.id,
            "set_id": self.set_id,
            "md5": self.md5,
            "artist": self.artist,
            "title": self.title,
            "version": self.version,
            "creator": self.creator,
            "last_update": self.last_update,
            "total_length": self.total_length,
            "max_combo": self.max_combo,
            "status": self.status,
            "mode": self.mode,
            "bpm": self.bpm,
            "cs": self.cs,
            "od": self.od,
            "ar": self.ar,
            "hp": self.hp,
            "star": self.star,
        }

    @classmethod
    async def from_sql(cls, md5: Optional[str], bid: Optional[int]) -> Optional["Beatmap"]:
        """
        Fetch a beatmap by md5 or bid from the database.
        Args:
            md5 (str): The MD5 hash of the beatmap.
            bid (int): The beatmap ID. 
        Returns:
            Optional[Beatmap]: The beatmap object if found, otherwise None.
        """
        query = f"""
        SELECT id, md5, set_id,
        artist, title, version, creator,
        last_update, total_length, max_combo,
        status,
        mode, bpm, cs, od, ar, hp,
        star
        FROM maps WHERE {"id" if bid else "md5"} = $1
        """
        params = [bid] if bid else [md5]
        if not (data := await glob.db.fetch(query, params)):
            return

        return cls(**data)

    async def save_to_sql(self) -> None:
        """
        Saves the beatmap object to the SQL database.
        If the beatmap already exists, it updates the existing record.
        """

        # Convert datetime objects to Unix timestamp integers
        last_update_int = (
            int(self.last_update.timestamp())
            if isinstance(self.last_update, datetime)
            else self.last_update
        )
        await glob.db.execute(
            "INSERT INTO maps ("
            "md5, id, set_id, "
            "artist, title, version, creator, "
            "last_update, total_length, max_combo, "
            "status, "
            "mode, bpm, cs, od, ar, hp, star"
            ") VALUES ("
            "$1, $2, $3, "
            "$4, $5, $6, $7, "
            "$8, $9, $10, "
            "$11, "
            "$12, $13, $14, $15, $16, $17, $18"
            ") ON CONFLICT (id) DO UPDATE SET "
            "md5 = EXCLUDED.md5, "
            "set_id = EXCLUDED.set_id, "
            "artist = EXCLUDED.artist, "
            "title = EXCLUDED.title, "
            "version = EXCLUDED.version, "
            "creator = EXCLUDED.creator, "
            "last_update = EXCLUDED.last_update, "
            "total_length = EXCLUDED.total_length, "
            "max_combo = EXCLUDED.max_combo, "
            "status = EXCLUDED.status, "
            "mode = EXCLUDED.mode, "
            "bpm = EXCLUDED.bpm, "
            "cs = EXCLUDED.cs, "
            "od = EXCLUDED.od, "
            "ar = EXCLUDED.ar, "
            "hp = EXCLUDED.hp, "
            "star = EXCLUDED.star",
            [
                self.md5,
                self.id,
                self.set_id,
                self.artist,
                self.title,
                self.version,
                self.creator,
                last_update_int,
                self.total_length,
                self.max_combo,
                self.status,
                self.mode,
                self.bpm,
                self.cs,
                self.od,
                self.ar,
                self.hp,
                self.star,
            ],
        )
    
    async def recalc_lb_placements(self) -> None:
        """
        Recalculates the local and global placements for the beatmap.
        This is useful when the beatmap's scores change and placements need to be updated.
        """
        from objects.score import Score
        scores = await glob.db.fetchall(
            """
            SELECT id, score, local_placement, global_placement, pp, playerid
            FROM scores
            WHERE md5 = $1
            """,
            [self.md5],
        )
        if not scores:
            return
        for score in scores:
            score["md5"] = self.md5
            score_obj = await Score.from_sql(0, score)
            score_obj.global_placement, score_obj.local_placement = await score_obj.calc_lb_placement()
            await glob.db.execute(
                "UPDATE scores SET global_placement = $1, local_placement = $2 WHERE id = $3",
                [score_obj.global_placement if score_obj.local_placement == 1 else 0, score_obj.local_placement, score_obj.id],
            )
