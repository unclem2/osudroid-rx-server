import re
import json

#TODO: move to lib
#TODO: fix differences between mod settings appearance 
class Mods:
    def __init__(self, mods):
        self.is_json = True
        try:
            self.mods = json.loads(mods)
        except json.JSONDecodeError:
            self.mods = mods
            self.is_json = False
    
    def __get_droid_encoded_mods(self, mods: str):
        mods = re.sub(r"\bx\d+\.\d+\b", "", mods, flags=re.IGNORECASE)

        mods = re.sub(r"[^a-z]", "", mods)
        return mods
    
    def __old_convert_std(self):
        mod_mapping = {
            "n": "NF",
            "e": "EZ",
            "h": "HD",
            "r": "HR",
            "u": "SD",
            "d": "DT",
            "x": "RX",
            "t": "HT",
            "c": "NC",
            "i": "FL",
            "v": "V2",
            "p": "AP",
            "a": "AT",
            "s": "PR",
            "l": "RE",
            "m": "SC",
            "f": "PF",
            "b": "TC",
        }

        mods = ""

        for char in self.__get_droid_encoded_mods(self.mods):
            if char in mod_mapping:
                mods += mod_mapping[char]

        matchar = re.search(r"\bAR(\d+\.\d+)\b", self.mods)
        matchcs = re.search(r"\bCS(\d+\.\d+)\b", self.mods)
        matchod = re.search(r"\bOD(\d+\.\d+)\b", self.mods)
        matchhp = re.search(r"\bHP(\d+\.\d+)\b", self.mods)
        matchsm = re.search(r"\bx(\d+\.\d+)\b", self.mods, re.IGNORECASE)
        matchfld = re.search(r"\bFLD(\d+\.\d+)\b", self.mods)

        if matchar or matchcs or matchod or matchhp:
            da = "DA"
            if matchar:
                da += f"AR{matchar.group(1)}"
            if matchcs:
                da += f"CS{matchcs.group(1)}"
            if matchod:
                da += f"OD{matchod.group(1)}"
            if matchhp:
                da += f"HP{matchhp.group(1)}"
            mods += da
        if matchsm:
            mods += f"CS({matchsm.group(1)})"
        if matchfld:
            mods += f"FLD({matchfld.group(1)})"
        
        return mods

    def __old_convert_droid(self):
        mod_mapping = {
            "n": {"acronym": "NF"},
            "e": {"acronym": "EZ"},
            "h": {"acronym": "HD"},
            "r": {"acronym": "HR"},
            "u": {"acronym": "SD"},
            "d": {"acronym": "DT"},
            "x": {"acronym": "RX"},
            "t": {"acronym": "HT"},
            "c": {"acronym": "NC"},
            "i": {"acronym": "FL"},
            "v": {"acronym": "V2"},
            "p": {"acronym": "AP"},
            "a": {"acronym": "AT"},
            "s": {"acronym": "PR"},
            "l": {"acronym": "RE"},
            "m": {"acronym": "SC"},
            "f": {"acronym": "PF"},
            "b": {"acronym": "TC"},
        }

        mods= []
        for char in self.__get_droid_encoded_mods(self.mods):
            if char in mod_mapping:
                mods.append(mod_mapping[char])

        matchar = re.search(r"\bAR(\d+\.\d+)\b", self.mods)
        matchcs = re.search(r"\bCS(\d+\.\d+)\b", self.mods)
        matchod = re.search(r"\bOD(\d+\.\d+)\b", self.mods)
        matchhp = re.search(r"\bHP(\d+\.\d+)\b", self.mods)
        matchsm = re.search(r"\bx(\d+\.\d+)\b", self.mods, re.IGNORECASE)
        matchfld = re.search(r"\bFLD(\d+\.\d+)\b", self.mods)

        if matchar or matchcs or matchod or matchhp:
            da = {
                "acronym": "DA",
                "settings": {}
            }
            if matchar:
                da["settings"]["ar"] = float(matchar.group(1))
            if matchcs:
                da["settings"]["cs"] = float(matchcs.group(1))
            if matchod:
                da["settings"]["od"] = float(matchod.group(1))
            if matchhp:
                da["settings"]["hp"] = float(matchhp.group(1))
            mods.append(da)

        if matchsm:
            mods.append({
                "acronym": "CS",
                "settings": {"rateMultiplier": float(matchsm.group(1))}
            })

        if matchfld:
            for i, mod in enumerate(mods):
                if mod["acronym"] == "FL":
                    mods[i] = {
                        "acronym": "FL",
                        "settings": {"areaFollowDelay": float(matchfld.group(1))}
                    }
                    break


        return mods


    @property
    def convert_std(self):
        if self.is_json == False:
            return self.__old_convert_std()
        ret = ""
        for mod in self.mods:
            ret += mod["acronym"]
            if "settings" in mod:
                for key, value in mod["settings"].items():
                    ret += f"({key}:{value})"
        return ret

    @property
    def convert_droid(self):
        if self.is_json == False:
            return self.__old_convert_droid()
        for mod in self.mods:
            if mod["acronym"] == "DA":
                if "settings" not in mod:
                    mod["settings"] = {}
                if "approach_rate" in mod["settings"]:
                    mod["settings"]["ar"] = mod["settings"].pop("approach_rate")
                if "circle_size" in mod["settings"]:
                    mod["settings"]["cs"] = mod["settings"].pop("circle_size")
                if "overall_difficulty" in mod["settings"]:
                    mod["settings"]["od"] = mod["settings"].pop("overall_difficulty")
                if "health_points" in mod["settings"]:
                    mod["settings"]["hp"] = mod["settings"].pop("health_points")
            if mod["acronym"] == "REZ":
                mod["acronym"] = "RE"
        return self.mods

    @property
    def convert_json(self):
        return json.dumps(self.convert_droid, separators=(",", ":"))

    def get_mod(self, acronym):
        for mod in self.convert_droid:
            if mod["acronym"] == acronym:
                return mod
        return None    

