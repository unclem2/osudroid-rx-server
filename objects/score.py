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

    # def __repr__(self) -> str:
    #     return {self.FAILED: "Failed", self.SUBMITTED: "Submitted", self.BEST: "Best"}[
    #         self.value
    #     ]


class Score:
    """
    i cant wrap my head around score submission so this one is based from gulag

    <3 cmyui
    """

    def __init__(self):
        self.id: int = 0
        self.bmap: Beatmap = None
        self.md5: str = ""
        self.player: Player = None

        self.pp: PPCalculator = None
        self.score: float = 0
        self.max_combo: int = 0
        self.mods: str = ""

        self.acc: float = 0

        self.h300: int = 0
        self.h100: int = 0
        self.h50: int = 0
        self.hmiss: int = 0
        self.hgeki: int = 0
        self.hkatsu: int = 0
        self.slidertickhits: int = 0
        self.sliderendhits: int = 0

        self.grade: str = ""

        self.local_placement: int = 0
        self.global_placement: int = 0
        self.fc: bool = None
        self.status: SubmissionStatus = SubmissionStatus.SUBMITTED
        self.date: int = 0

        self.prev_best: Score = None

    @classmethod
    async def from_sql(cls, score_id: int, res=None):
        if res is None:
            res = await glob.db.fetch("SELECT * FROM scores WHERE id = $1", [score_id])
        if not res:
            return

        s = cls()

        s.id = res.get("id", 0)
        s.bmap = await Beatmap.from_md5(res.get("md5", "")) if res.get("md5") else None
        s.player = glob.players.get(id=int(res.get("playerid", 0))) if res.get("playerid") else None
        s.status = SubmissionStatus(res.get("status", SubmissionStatus.SUBMITTED))
        s.md5 = res.get("md5", "")

        s.score = res.get("score", 0)
        s.max_combo = res.get("combo", 0)
        s.mods = res.get("mods", 0)
        s.acc = res.get("acc", 0.0)
        s.grade = res.get("grade", "")

        s.h300 = res.get("hit300", 0)
        s.h100 = res.get("hit100", 0)
        s.h50 = res.get("hit50", 0)
        s.hmiss = res.get("hitmiss", 0)
        s.hgeki = res.get("hitgeki", 0)
        s.hkatsu = res.get("hitkatsu", 0)
        
        s.date = int(res.get("date", 0))
        s.pp = await PPCalculator.from_score(s)
        if s.bmap and s.pp is not False:
            s.pp.calc_pp = float(res.get("pp", 0))
        else:
            s.pp = PPCalculator()
            s.pp.calc_pp = float(res.get("pp", 0))
            s.status = SubmissionStatus.FAILED

        if s.md5:
            s.global_placement = res.get("global_placement", 0)
            s.local_placement = res.get("local_placement", 0)

        return s

    @classmethod
    async def from_submission(cls, data: dict):
        data = data.split(" ")

        s = cls()
        pname = data[13] if glob.config.legacy else data[15]
        s.player = glob.players.get(username=pname)

        if not s.player:
            # refer to gulag score.py
            return s

        if not s.player.stats.playing:
            raise Exception(
                "Failed to get the map user played. Maybe the server restarted?"
            )

        s.md5 = s.player.stats.playing

        if s.md5:
            s.bmap = await Beatmap.from_md5(s.md5)
            
        s.mods = data[0]
        (s.score, s.max_combo) = map(int, data[1:3])
        s.grade = data[3]
        (s.hgeki, s.h300, s.hkatsu, s.h100, s.h50, s.hmiss) = map(int, data[4:10])

        if glob.config.legacy:
            s.acc = float(data[10]) / 1000 if glob.config.legacy else float(data[10]) * 100
            s.date = int(data[11])  # 1.6.8: Int?
            s.fc = (data[12] == "true") or (data[12] == "1")  # 1.6.8 Fix
        else:
            s.slidertickhits = int(data[10])
            s.sliderendhits = int(data[11])
            s.acc = float(data[12]) * 100
            s.date = int(data[13])
            s.fc = (data[14] == "true") or (data[14] == "1")  # 1.6.8 Fix

        s.pp = await PPCalculator.from_score(s)

        if s.bmap and s.pp is not False:
            await s.pp.calc()
            await s.calc_status()
            s.global_placement, s.local_placement = await s.calc_lb_placement()
        else:
            s.pp = PPCalculator()
            s.pp.calc_pp = 0.0
            s.status = SubmissionStatus.SUBMITTED

        return s

    @property
    def as_json(self):
        return {
            "id": self.id,
            "bmap": self.bmap.as_json if self.bmap else None,
            "md5": self.md5,
            "player": self.player.as_json if self.player else "",
            "pp": self.pp.calc_pp if self.pp else 0.0,
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
            "local_placement": self.local_placement,
            "global_placement": self.global_placement,
            "fc": self.fc,
            "status": self.status,
            "date": self.date,
        }

    async def calc_lb_placement(self):
        global_p = await glob.db.fetch(
            "SELECT count(*) as c FROM scores WHERE md5 = $1 AND pp > $2 AND status = 2",
            [self.md5, self.pp.calc_pp],
        )
        global_rank = int(global_p["c"]) + 1 if global_p else 1

        local_p = await glob.db.fetch(
            "SELECT count(*) as c FROM scores WHERE md5 = $1 AND playerID = $2 AND pp > $3",
            [self.md5, self.player.id, self.pp.calc_pp],
        )
        local_rank = int(local_p["c"]) + 1 if local_p else 1
        return global_rank, local_rank

    async def calc_status(self):

        res = await glob.db.fetch(
            "SELECT * FROM scores WHERE playerID = $1 AND md5 = $2 AND status= $3",
            [self.player.id, self.md5, 2],
        )

        if res:
            self.prev_best = await Score.from_sql(res["id"])

            if self.pp.calc_pp > res["pp"]:
                self.status = SubmissionStatus.BEST
                self.prev_best.status = SubmissionStatus.SUBMITTED
                await glob.db.execute(
                    "UPDATE scores SET status = $1 WHERE id = $2", [1, res["id"]]
                )
        else:
            self.status = SubmissionStatus.BEST


