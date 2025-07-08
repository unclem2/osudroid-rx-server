import logging
from objects import glob
from objects.beatmap import Beatmap
import rosu_pp_py as osu_pp
import math
import objects.mods as Mods


class PPCalculator:
    def __init__(self, **kwargs):
        self.mods = kwargs.get("mods", [])
        self.bm_path = kwargs.get("bm_path")
        self.h300 = kwargs.get("h300", 0)
        self.h100 = kwargs.get("h100", 0)
        self.h50 = kwargs.get("h50", 0)
        self.hmiss = kwargs.get("hmiss", 0)
        self.max_combo = kwargs.get("max_combo", 0)
        self.acc = kwargs.get("acc", 0.0)
        self.calc_pp = None
  

    @classmethod
    async def from_score(cls, score):
        if not glob.config.pp:
            return False

        if not (bmap := await Beatmap.from_md5(score.map_hash)):
            logging.error(f"Failed to get map: {score.map_hash}")
            return False

        res = await bmap.download()
        if not res:
            return False

        return cls(**{"bm_path": res, **score.as_json})


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

        if self.acc is not 0.0:
            performance.set_accuracy(self.acc)
        else:
            performance.set_n300(self.h300)
            performance.set_n100(self.h100)
            performance.set_n50(self.h50)
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

        pp_return = aim_pp * force_ar_penalty * miss_penality_aim
        if float(pp_return) >= float(glob.config.max_pp_value):
            return 0

        logging.debug(
            f"PP Calculation: Aim PP: {aim_pp}, Force AR Penalty: {force_ar_penalty}, "
            f"Miss Penalty Aim: {miss_penality_aim}, Final PP: {pp_return}"
        )

        self.calc_pp = pp_return
        return pp_return


