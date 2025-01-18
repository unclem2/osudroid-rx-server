import logging
from objects import glob
from objects.beatmap import Beatmap
import rosu_pp_py as osu_pp
import math
import objects.mods as Mods
import oppadc


class PPCalculator:
    def __init__(self, path):
        self.bm_path = path
        self.acc = 100
        self.hmiss = 0
        self.max_combo = 0
        self.mods = ""
        self.calc_pp = 0.0

    @classmethod
    async def from_md5(cls, md5: str, **kwargs):
        if not glob.config.pp:
            return False

        if not (bmap := await Beatmap.from_md5(md5)):
            logging.error(f"Failed to get map: {md5}")
            return False

        res = await bmap.download()
        if not res:
            return False

        return cls(res, **kwargs)

    async def calc(self):
        # Get the speed multiplier for the mods

        mods = Mods.Mods(self.mods)
        speed_multiplier = mods.speed_multiplier
        if speed_multiplier is None:
            speed_multiplier = 1
        speed_multiplier = float(speed_multiplier)

        force_ar = mods.forcear
        force_cs = mods.forcecs
        fl_delay = mods.fldelay

        mods = mods.convert_droid

        if force_cs is not None:
            return 0
        if fl_delay is not None:
            return 0

        # Read the beatmap content
        beatmap_content = self.bm_path.read_text()
        beatmap = osu_pp.Beatmap(content=beatmap_content)
        original_od = beatmap.od - 4

        applied = None

        if speed_multiplier != 1:
            for i, mod in enumerate(mods):
                if mod["acronym"] == "DT":
                    mods[i] = {
                        "acronym": "DT",
                        "settings": {"speed_change": 1.5 * speed_multiplier},
                    }
                    applied = True
                    break
                elif mod["acronym"] == "HT":
                    mods[i] = {
                        "acronym": "HT",
                        "settings": {"speed_change": 0.75 * speed_multiplier},
                    }
                    applied = True
                    break
                elif mod["acronym"] == "NC":
                    mods[i] = {
                        "acronym": "NC",
                        "settings": {"speed_change": 1.5 * speed_multiplier},
                    }
                    applied = True
                    break

        # Create the performance object
        performance = osu_pp.Performance(
            accuracy=self.acc,
            mods=mods,
            misses=self.hmiss,
            combo=self.max_combo,
        )
        if applied != True and speed_multiplier != 1:
            performance.set_clock_rate(speed_multiplier)

        performance.set_od(original_od, od_with_mods=True)

        for i, mod in enumerate(mods):
            if mod["acronym"] == "PR":
                original_od += 4
                performance.set_od(original_od, od_with_mods=False)
            if mod["acronym"] == "AP":
                return 0
            if mod["acronym"] == "REZ":
                original_od = original_od / 2
                performance.set_cs(beatmap.cs * 0.66, cs_with_mods=False)
                performance.set_ar(beatmap.ar - 0.5, ar_with_mods=True)
                performance.set_od(original_od, od_with_mods=False)

        # Calculate performance attributes
        attributes = performance.calculate(beatmap)

        try:
            speed_reduction = attributes.pp_speed / attributes.pp
        except ZeroDivisionError:
            return 0

        speed_reduction_factor = math.exp(-speed_reduction)

        ar_bonus = 1
        if attributes.difficulty.ar > 10.33:
            ar_bonus = 1 + (attributes.difficulty.ar - 10.33) * 0.4
        if attributes.difficulty.ar < 8:
            ar_bonus = 1 + (8 - attributes.difficulty.ar) * 0.4

        force_ar_penalty = 1
        if force_ar is not None:
            force_ar_penalty = 0

        # Calculate and return the final pp value
        aim_pp = attributes.pp_aim * ar_bonus
        amount_hitobjects = (
            attributes.difficulty.n_circles
            + attributes.difficulty.n_sliders
            + attributes.difficulty.n_spinners
        )
        miss_penality_aim = 0.97 * pow(
            1 - pow(self.hmiss / amount_hitobjects, 0.775), self.hmiss
        )

        pp_return = (
            aim_pp * speed_reduction_factor * force_ar_penalty * miss_penality_aim
        )
        if float(pp_return) >= float(glob.config.max_pp_value):
            return 0
        self.calc_pp = pp_return
        return pp_return


async def recalc_scores():
    """never use this unless something fucked up/testing"""
    print("recalculatin sk0r3")

    scores = await glob.db.fetchall("SELECT * FROM scores ORDER BY id ASC LIMIT 100")
    for score in scores:
        m = await PPCalculator.from_md5(score["maphash"])
        if m:
            m.acc = score["acc"]
            m.hmiss = score["hitmiss"]
            m.max_combo = score["combo"]
            m.mods = score["mods"]

            await m.calc()

            print(score["id"], score["maphash"], m.calc_pp)

            await glob.db.execute(
                "UPDATE scores SET pp = $1 WHERE id = $2", [m.calc_pp, score["id"]]
            )


async def recalc_single_score(score_id: int):
    """recalculate a single score"""
    score = await glob.db.fetch(
        "SELECT * FROM scores WHERE id = $1 ORDER BY id ASC LIMIT 100", [score_id]
    )

    m = await PPCalculator.from_md5(score["maphash"])
    if m:
        m.acc = score["acc"]
        m.hmiss = score["hitmiss"]
        m.max_combo = score["combo"]
        m.mods = score["mods"]

        await m.calc()

        print(score["id"], score["maphash"], m.calc_pp)

        await glob.db.execute(
            "UPDATE scores SET pp = $1 WHERE id = $2", [m.calc_pp, score["id"]]
        )
