import json
import logging
from objects import glob
from objects.beatmap import Beatmap
import rosu_pp_py as osu_pp
import math
from osudroid_api_wrapper import ModList


def droid_cs_to_standard_cs(cs: float) -> float:
    """
        Converts Droid CS to standard CS.
        Formulas taken from Rian8337 osu-droid-module:
        https://github.com/Rian8337/osu-droid-module/blob/master/packages/osu-base/src/utils/CircleSizeCalculator.ts
    """
    old_assumed_droid_height = 681
    base_radius = 64
    old_droid_scale_multiplier = (0.5 * (11 - 5.2450170716245195)) / 5
    broken_gamefield_rounding_allowance = 1.00041

    old_droid_scale = max(
        ((old_assumed_droid_height / 480) * (54.42 - cs * 4.48)) / base_radius + old_droid_scale_multiplier,
        1e-3
    )

    standard_radius = (base_radius * old_droid_scale) / ((old_assumed_droid_height * 0.85) / 384)

    scale = standard_radius / base_radius

    standard_cs = 5 + (5 * (1 - (2 * scale) / broken_gamefield_rounding_allowance)) / 0.7
    return standard_cs 


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
        self.difficulty = 0
        self.calc_pp = None
  

    @classmethod
    async def from_score(cls, score):
        if not glob.config.pp:
            return False

        if not (bmap := await Beatmap.from_md5(score.md5)):
            logging.error(f"Failed to get map: {score.md5}")
            return False

        res = await bmap.download()
        if not res:
            return False

        return cls(**{"bm_path": res, **score.as_json})


    async def calc(self, api=False):

        if isinstance(self.mods, list):
            mods = ModList.from_dict(self.mods)
        elif isinstance(self.mods, str):
            mods = ModList.from_dict(json.loads(self.mods))

        speed_multiplier = mods.get_mod("CS")
        if speed_multiplier is None:
            speed_multiplier = 1
        else:
            speed_multiplier = speed_multiplier.settings.get_setting("rateMultiplier").value

        if mods.get_mod("RX") is None:
            self.calc_pp = 0
            return 0
        if mods.get_mod("AP") is not None:
            self.calc_pp = 0
            return 0
        if mods.get_mod("DA") is not None:
            self.calc_pp = 0
            return 0
        if mods.get_mod("WD") is not None:
            self.calc_pp = 0
            return 0
        if mods.get_mod("WU") is not None:
            self.calc_pp = 0
            return 0
    

        # Read the beatmap content
        beatmap_content = self.bm_path.read_text()
        beatmap = osu_pp.Beatmap(content=beatmap_content)
        original_od = beatmap.od - 4
        cs = beatmap.cs
        applied = None

        submit_mods = mods.as_calculable_mods
        if speed_multiplier != 1:
            for i, mod in enumerate(submit_mods):
                if mod["acronym"] == "DT":
                    submit_mods[i] = {
                        "acronym": "DT",
                        "settings": {"speed_change": 1.5 * speed_multiplier},
                    }
                    applied = True
                    break
                elif mod["acronym"] == "HT":
                    submit_mods[i] = {
                        "acronym": "HT",
                        "settings": {"speed_change": 0.75 * speed_multiplier},
                    }
                    applied = True
                    break
                elif mod["acronym"] == "NC":
                    submit_mods[i] = {
                        "acronym": "NC",
                        "settings": {"speed_change": 1.5 * speed_multiplier},
                    }
                    applied = True
                    break

        # print(mods)
        performance = osu_pp.Performance(
            mods=submit_mods

        )

        beatmap_attrs = osu_pp.BeatmapAttributesBuilder(
            mods=submit_mods,
            map=beatmap
        )

        if applied != True and speed_multiplier != 1:
            performance.set_clock_rate(speed_multiplier)
            beatmap_attrs.set_clock_rate(speed_multiplier)

        performance.set_od(original_od, od_with_mods=False)
        beatmap_attrs.set_od(original_od, od_with_mods=False)
        
        for i, mod in enumerate(mods.as_calculable_mods):
            if mod["acronym"] == "PR":
                original_od += 4
                performance.set_od(original_od, od_with_mods=False)
                beatmap_attrs.set_od(original_od, od_with_mods=False)
            if mod["acronym"] == "RE":
                original_od = original_od / 2
                cs *= 0.5
                performance.set_ar(beatmap.ar - 0.5, ar_with_mods=True)
                performance.set_od(original_od, od_with_mods=False)
                performance.set_cs(cs, cs_with_mods=False)

                beatmap_attrs.set_ar(beatmap.ar - 0.5, ar_with_mods=True)
                beatmap_attrs.set_od(original_od, od_with_mods=False)
                beatmap_attrs.set_cs(cs, cs_with_mods=False)

        

        # cs = droid_cs_to_standard_cs(cs)
        # performance.set_cs(cs, cs_with_mods=False)

        if api == True:
            performance.set_accuracy(self.acc)
        else:
            performance.set_n300(self.h300)
            performance.set_n100(self.h100)
            performance.set_n50(self.h50)
        performance.set_misses(self.hmiss)
        performance.set_combo(self.max_combo)
        attributes = performance.calculate(beatmap)
        

        beatmap_attrs = beatmap_attrs.build()

        ar_bonus = 0.0

        if beatmap_attrs.ar > 10.33:
            ar_bonus += 0.4 * (beatmap_attrs.ar - 10.33)

        elif beatmap_attrs.ar < 8.0:
            ar_bonus += 0.01 * (8.0 - beatmap_attrs.ar)


        pp_return = attributes.pp * (1+min(ar_bonus, ar_bonus * (beatmap.n_objects / 1000)))

        if float(pp_return) >= float(glob.config.max_pp_value):
            self.calc_pp = 0
            return 0

        if api == True:
            self.difficulty = attributes.difficulty.stars
        self.calc_pp = pp_return
        return pp_return


