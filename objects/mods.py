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
            "l": "REZ",
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
            "l": {"acronym": "REZ"},
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
                da["settings"]["approach_rate"] = float(matchar.group(1))
            if matchcs:
                da["settings"]["circle_size"] = float(matchcs.group(1))
            if matchod:
                da["settings"]["overall_difficulty"] = float(matchod.group(1))
            if matchhp:
                da["settings"]["drain_rate"] = float(matchhp.group(1))
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
                if "ar" in mod["settings"]:
                    mod["settings"]["approach_rate"] = mod["settings"].pop("ar")
                if "cs" in mod["settings"]:
                    mod["settings"]["circle_size"] = mod["settings"].pop("cs")
                if "od" in mod["settings"]:
                    mod["settings"]["overall_difficulty"] = mod["settings"].pop("od")
                if "hp" in mod["settings"]:
                    mod["settings"]["drain_rate"] = mod["settings"].pop("hp")
        return self.mods

    def get_mod(self, acronym):
        for mod in self.convert_droid:
            if mod["acronym"] == acronym:
                return mod
        return None    
