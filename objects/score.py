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
        s.pp = await PPCalculator.from_md5(s.map_hash)
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
            s.pp = await PPCalculator.from_md5(s.map_hash)

        (s.score, s.max_combo) = map(int, data[1:3])
        (s.hgeki, s.h300, s.hkatsu, s.h100, s.h50, s.hmiss) = map(int, data[4:10])

        s.mods = data[0]
        s.grade = data[3]
        s.acc = float(data[10]) / 1000 if glob.config.legacy else float(data[10]) * 100
        s.fc = (data[12] == "true") or (data[12] == "1")  # 1.6.8 Fix
        s.date = int(data[11])  # 1.6.8: Int?

        if s.bmap and s.pp is not False:
            s.pp.hit300 = s.h300
            s.pp.hit100 = s.h100
            s.pp.hit50 = s.h50
            s.pp.hmiss = s.hmiss
            s.pp.max_combo = s.max_combo
            s.pp.mods = s.mods
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
                        s.pp = await PPCalculator.from_md5(maphash)
                        s.acc = user_map_score["acc"]
                        s.hmiss = user_map_score["hitmiss"]
                        s.max_combo = user_map_score["combo"]
                        s.mods = user_map_score["mods"]
                        s.player = player

                if s.pp == False:
                    print(f"{player.id} - failed to load map {maphash}")
                    continue
                s.pp.acc = s.acc
                s.pp.hmiss = s.hmiss
                s.pp.max_combo = s.max_combo
                s.pp.mods = s.mods
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
