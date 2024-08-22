import { Accuracy, MapInfo, MapStats, ModUtil, BeatmapDecoder } from "@rian8337/osu-base";
import {
    DroidDifficultyCalculator,
    DroidPerformanceCalculator,
    OsuDifficultyCalculator,
    OsuPerformanceCalculator
} from "@rian8337/osu-difficulty-calculator";
import { readFile } from "fs";

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

readFile(`data/beatmaps/${mapid}.osu`, { encoding: "utf-8" }, (err, data) => {
    if (err) throw err;

    const decoder = new BeatmapDecoder().decode(data);

    // console.log(decoder.result.hitObjects);
    const accuracy = new Accuracy({
        nmiss: misses_args,
        nobjects: decoder.result.hitObjects._circles + decoder.result.hitObjects._sliders + decoder.result.hitObjects._spinners,
        percent: accuracy_args,
        
    });
    // console.log(accuracy);
    const nmrating = new OsuDifficultyCalculator(decoder.result).calculate({
        mods: mods,
    });

    const nmperformance = new OsuPerformanceCalculator(nmrating.attributes).calculate({
        accPercent: accuracy,
        combo: combo
    });
    // console.log(nmperformance);
    const pp_return = nmperformance.total - nmperformance.speed;
    console.log(pp_return);
});