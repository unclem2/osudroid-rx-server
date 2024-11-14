import logging
from pathlib import Path
from objects import glob
from objects.beatmap import Beatmap
import re
from objects.player import Player
import rosu_pp_py as osu_pp
import math

def convert_droid(mods: str):
    mod_mapping = {
        'nm': {"acronym": ""},
        'n': {"acronym": "NF"},
        'e': {"acronym": "EZ"},
        'h': {"acronym": "HD"},
        'r': {"acronym": "HR"},
        'u': {"acronym": "SD"},
        'd': {"acronym": "DT"},
        'x': {"acronym": ""},
        't': {"acronym": "HT"},
        'c': {"acronym": "NC"},
        'i': {"acronym": "FL"},
        'v': {"acronym": "V2"},
        'p': {"acronym": "AP"},
        'a': {"acronym": "AT"},
        's': {"acronym": "PR"},
        'l': {"acronym": "REZ"},
        'm': {"acronym": "SC"},
        'f': {"acronym": "PF"},
        'b': {"acronym": "SU"}
    }
    
    used_mods = []
    pr = None
    
    for char in mods:
        if char in mod_mapping:
            if char == 's':
                pr = True
                continue
            used_mods.append(mod_mapping[char])
    
    return used_mods, pr


def get_multiplier(mods):
    """
    Extracts the multiplier value from the mods string.
    For example, 'xs|x2.00' will return 'x2.00'.
    """
    match = re.search(r'\bx(\d+\.\d+)\b', mods, re.IGNORECASE)
    return match.group(1) if match else None

def get_forcear(mods):
    match = re.search(r'\bAR(\d+\.\d+)\b', mods)
    
    return match.group(1) if match else None

def get_forcecs(mods):
    match = re.search(r'\bCS(\d+\.\d+)\b', mods)
    
    return match.group(1) if match else None 

def get_fldelay(mods):
    match = re.search(r'\bFLD(\d+\.\d+)\b', mods)
    
    return match.group(1) if match else None  

def get_used_mods(mods):
    """
    Removes unwanted characters from the mods string.
    """
    mods = re.sub(r'\bx\d+\.\d+\b', '', mods, flags=re.IGNORECASE)

    mods = re.sub(r'[^a-zA-Z]', '', mods)
    return mods

class PPCalculator:
    def __init__(self, path):
            self.bm_path = path


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
 
    async def calc(self, s):
        # Get the speed multiplier for the mods
        speed_multiplier = get_multiplier(s.mods)
        if speed_multiplier is None:
            speed_multiplier = 1
        speed_multiplier = float(speed_multiplier)
        
        force_ar = get_forcear(s.mods)
        force_cs = get_forcecs(s.mods)
        fl_delay = get_fldelay(s.mods)

        if force_cs is not None:
            return 0  
        if fl_delay is not None:
            return 0
        
        # Get and convert the used mods
        mods = get_used_mods(s.mods)
        mods, pr = convert_droid(mods)

        # Read the beatmap content
        beatmap_content = self.bm_path.read_text()
        beatmap = osu_pp.Beatmap(content=beatmap_content)
        original_od = beatmap.od
        
        # Adjust OD if PR mod is present
        if pr:
            original_od += 4

        # Adjust speed change settings for DT and HT mods
        applied = None

                
        if speed_multiplier != 1:
            
            for i, mod in enumerate(mods):
                if mod['acronym'] == 'DT':
                    mods[i] = {
                        'acronym': 'DT',
                        "settings": {
                            "speed_change": 1.5 * speed_multiplier
                        }
                    }
                    applied =True
                    break
                elif mod['acronym'] == 'HT':
                    mods[i] = {
                        'acronym': 'HT',
                        "settings": {
                            "speed_change": 0.75 * speed_multiplier
                        }
                    }
                    applied = True
                    break
                elif mod['acronym'] == 'NC':
                    mods[i] = {
                        'acronym': 'NC',
                        "settings": {
                            "speed_change": 1.5*speed_multiplier
                        }
                    }
                    applied = True
                    break

      
        # Create the performance object
        performance = osu_pp.Performance(
            accuracy=s.acc,
            mods=mods,
            misses=s.hmiss,
            combo=s.max_combo,
            
        )
        if applied != True and speed_multiplier != 1:
            performance.set_clock_rate(speed_multiplier)
        # performance.set_cs(beatmap.cs-2, cs_with_mods = False)
        for i, mod in enumerate(mods):
            if mod['acronym'] == 'REZ':
                performance.set_ar(beatmap.ar-0.5, ar_with_mods = False)
                original_od = original_od - 4
                performance.set_od(original_od, od_with_mods = False)
                performance.set_cs(beatmap.cs-3, cs_with_mods = False)
                for i, mod in enumerate(mods):
                    if mod['acronym'] == 'EZ':
                        performance.set_ar(beatmap.ar-1, ar_with_mods = False)
                        original_od = original_od - 4
                        performance.set_od(original_od, od_with_mods = False)
                        performance.set_cs(beatmap.cs-4, cs_with_mods = False)
                        mods.pop(i)
            if mod['acronym'] == 'AP':
                return 0
        performance.set_od(original_od-4, od_with_mods = False)
        # Calculate performance attributes
        attributes = performance.calculate(beatmap)

        acc_factor = (100-s.acc)/30
        acc_factor = math.exp(-acc_factor)
        
        speed_reduction = attributes.pp_speed/attributes.pp
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
        pp_return = attributes.pp - attributes.pp_speed - attributes.pp_aim + aim_pp
        pp_return = pp_return * acc_factor * speed_reduction_factor * force_ar_penalty
        return pp_return

async def recalc_scores():
    ''' never use this unless something fucked up/testing '''
    print('recalculatin sk0r3')

    scores = await glob.db.fetchall('SELECT * FROM scores')
    for score in scores:
        m = await PPCalculator.from_md5(score['maphash'])
        if m:
            
            m.acc = score['acc']
            m.hmiss = score['hitmiss']
            m.max_combo = score['combo']
            m.bmap = await Beatmap.from_md5(score['maphash'])
            m.mods = score['mods']
            pp = await m.calc(m)

            print(score['id'], score['maphash'], pp)

            await glob.db.execute("UPDATE scores SET pp = $1 WHERE id = $2", [pp, score['id']])

async def recalc_stats():
    # Fetch players from the database
    players = await glob.db.fetchall("SELECT id FROM users")

    for player in players:
        # Assuming you have a Player class that can update stats
        player_obj = Player(id=int(player['id']))
        await player_obj.update_stats()