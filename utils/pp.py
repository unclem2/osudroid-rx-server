import logging
from objects import glob
from objects.beatmap import Beatmap
import rosu_pp_py as osu_pp
import math
import objects.mods as Mods


class PPCalculator:
    def __init__(self, path):
        self.bm_path = path
        self.hit300 = 0
        self.hit100 = 0
        self.hit50 = 0
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

        performance = osu_pp.Performance(
            mods=mods,
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


        performance.set_n300(self.hit300)
        performance.set_n100(self.hit100)
        performance.set_n50(self.hit50)
        performance.set_misses(self.hmiss)
        performance.set_combo(self.max_combo)
        attributes = performance.calculate(beatmap)


        force_ar_penalty = 1
        if force_ar is not None:
            force_ar_penalty = 0

        aim_pp = attributes.pp_aim * 1.1
        amount_hitobjects = (
            attributes.difficulty.n_circles
            + attributes.difficulty.n_sliders
            + attributes.difficulty.n_spinners
        )
        miss_penality_aim = 0.99 * pow(
            1 - pow(self.hmiss / amount_hitobjects, 0.775), self.hmiss - 10
        )
        if miss_penality_aim > 0.99:
            miss_penality_aim = 0.99

        pp_return = (
            aim_pp * force_ar_penalty * miss_penality_aim
        )
        if float(pp_return) >= float(glob.config.max_pp_value):
            return 0
        
        self.calc_pp = pp_return
        return pp_return


async def recalc_single_score(score_id: int):
    """recalculate a single score"""
    score = await glob.db.fetch(
        "SELECT * FROM scores WHERE id = $1 ORDER BY id ASC LIMIT 100", [score_id]
    )

    m = await PPCalculator.from_md5(score["maphash"])
    if m:
        m.hit300 = score["hit300"]
        m.hit100 = score["hit100"]
        m.hit50 = score["hit50"]
        m.hmiss = score["hitmiss"]
        m.max_combo = score["combo"]
        m.mods = score["mods"]

        await m.calc()

        print(score["id"], score["maphash"], m.calc_pp)

        # await glob.db.execute(
        #     "UPDATE scores SET pp = $1 WHERE id = $2", [m.calc_pp, score["id"]]
        # )
