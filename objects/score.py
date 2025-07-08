from objects.player import Player
from objects import glob
from enum import IntEnum, unique
from objects.beatmap import Beatmap
from utils.pp import PPCalculator


@unique
class SubmissionStatus(IntEnum):
    # totally not copied from gulag
    FAILED = 0
    SUBMITTED = 1
    BEST = 2

    def __repr__(self) -> str:
        return {self.FAILED: "Failed", self.SUBMITTED: "Submitted", self.BEST: "Best"}[
            self.value
        ]


class Score:
    """
    i cant wrap my head around score submission so this one is based from gulag

    <3 cmyui
    """

    def __init__(self):
        self.id: int = 0
        self.bmap: Beatmap = None
        self.map_hash: str = ""
        self.player: Player = None

        self.pp: PPCalculator = None
        self.score: float = 0
        self.max_combo: int = 0
        self.mods: int = 0

        self.acc: float = 0

        self.h300: int = 0
        self.h100: int = 0
        self.h50: int = 0
        self.hmiss: int = 0
        self.hgeki: int = 0
        self.hkatsu: int = 0
        self.grade: str = ""

        self.rank: str = ""
        self.fc: bool = None
        self.status: SubmissionStatus = SubmissionStatus.SUBMITTED
        self.date: str = ""

        self.prev_best: Score = None

    @classmethod
    async def from_sql(cls, score_id: int):
        res = await glob.db.fetch("SELECT * FROM scores WHERE id = $1", [score_id])
        if not res:
            return

        s = cls()

        s.id = res["id"]
        s.bmap = await Beatmap.from_md5(res["maphash"])
        s.player = glob.players.get(id=int(res["playerid"]))
        s.status = SubmissionStatus(res["status"])
        s.map_hash = res["maphash"]

        s.score = res["score"]
        s.max_combo = res["combo"]
        s.mods = res["mods"]
        s.acc = res["acc"]
        s.grade = res["rank"]

        s.h300 = res["hit300"]
        s.h100 = res["hit100"]
        s.h50 = res["hit50"]
        s.hmiss = res["hitmiss"]
        s.hgeki = res["hitgeki"]
        s.hkatsu = res["hitkatsu"]
        s.date = res["date"]
        s.pp = await PPCalculator.from_score(s)
        s.pp.calc_pp = int(round(res["pp"]))

        if s.map_hash:
            s.rank = await s.calc_lb_placement()

        return s

    @classmethod
    async def from_submission(cls, data: dict):
        data = data.split(" ")

        s = cls()
        pname = data[13]
        s.player = glob.players.get(name=pname)

        if not s.player:
            # refer to gulag score.py
            return s

        if not s.player.stats.playing:
            raise Exception(
                "Failed to get the map user played. Maybe the server restarted?"
            )

        s.map_hash = s.player.stats.playing

        if s.map_hash:
            s.bmap = await Beatmap.from_md5(s.map_hash)
            

        (s.score, s.max_combo) = map(int, data[1:3])
        (s.hgeki, s.h300, s.hkatsu, s.h100, s.h50, s.hmiss) = map(int, data[4:10])

        s.mods = data[0]
        s.grade = data[3]
        s.acc = float(data[10]) / 1000 if glob.config.legacy else float(data[10]) * 100
        s.fc = (data[12] == "true") or (data[12] == "1")  # 1.6.8 Fix
        s.date = int(data[11])  # 1.6.8: Int?

        s.pp = await PPCalculator.from_score(s)

        if s.bmap and s.pp is not False:
            await s.pp.calc()
            await s.calc_status()
            s.rank = await s.calc_lb_placement()
        else:
            s.pp = PPCalculator("")
            s.pp.calc_pp = 0.0
            s.status = SubmissionStatus.SUBMITTED

        return s

    @property
    def as_json(self):
        return {
            "id": self.id,
            "bmap": self.bmap.as_json,
            "map_hash": self.map_hash,
            "player": self.player.name,
            "pp": self.pp,
            "score": self.score,
            "max_combo": self.max_combo,
            "mods": self.mods,
            "acc": self.acc,
            "h300": self.h300,
            "h100": self.h100,
            "h50": self.h50,
            "hmiss": self.hmiss,
            "hgeki": self.hgeki,
            "hkatsu": self.hkatsu,
            "grade": self.grade,
            "rank": self.rank,
            "fc": self.fc,
            "status": self.status,
            "date": self.date,
        }

    async def calc_lb_placement(self):
        res = await glob.db.fetch(
            "SELECT count(*) as c FROM scores WHERE mapHash = $1 AND pp > $2 AND status = 2",
            [self.map_hash, self.pp.calc_pp],
        )
        return int(res["c"]) + 1 if res else 1

    async def calc_status(self):
        # res = await glob.db.userScore(id=self.player.id, mapHash=self.mapHash)
        try:
            res = await glob.db.fetch(
                "SELECT * FROM scores WHERE playerID = $1 AND mapHash = $2 AND status= $3",
                [self.player.id, self.map_hash, 2],
            )
        except:
            res = None
        if res:
            self.prev_best = await Score.from_sql(res["id"])

            if self.pp.calc_pp > res["pp"]:
                self.status = SubmissionStatus.BEST
                self.prev_best.status = SubmissionStatus.SUBMITTED
                await glob.db.execute(
                    "UPDATE scores SET status = $1 WHERE id = $2", [1, res["id"]]
                )
                print(
                    f"score {self.id} status changed from 2 to 1, prev best on map {res['pp']} new best on map {self.pp.calc_pp}"
                )
        else:
            self.status = SubmissionStatus.BEST


