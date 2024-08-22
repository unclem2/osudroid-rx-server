import { Accuracy, MapInfo, MapStats, ModUtil } from "@rian8337/osu-base";
import {
    DroidDifficultyCalculator,
    DroidPerformanceCalculator,
    OsuDifficultyCalculator,
    OsuPerformanceCalculator
} from "@rian8337/osu-difficulty-calculator";

const args = process.argv.slice(2);
if (args.length < 5) {
    console.error('Please provide mapid, mods, accuracy, misses, and combo as command-line arguments.');
    process.exit(1);
}

const mapid = parseInt(args[0], 10);
const mods_arg = args[1];
const accuracy_args = parseFloat(args[2]);
const misses_args = parseInt(args[3], 10);
const combo = parseInt(args[4], 10);
const mods = ModUtil.droidStringToMods(mods_arg);

if (isNaN(mapid) || isNaN(accuracy_args) || isNaN(misses_args) || isNaN(combo)) {
    console.error('One or more provided arguments are not valid numbers.');
    process.exit(1);
}

const beatmapInfo = await MapInfo.getInformation(mapid);

const accuracy = new Accuracy({
    nmiss: misses_args,
    percent: accuracy_args,
    nobjects: beatmapInfo.objects,
});


const nmrating = new OsuDifficultyCalculator(beatmapInfo.beatmap).calculate
({
    mods: mods,
});
const nmperformance = new OsuPerformanceCalculator(nmrating.attributes).calculate(
    {
        accPercent: accuracy,
        combo: combo
    });

const pp_return = nmperformance.total - nmperformance.speed;
console.log(pp_return);