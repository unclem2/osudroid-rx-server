import { Accuracy, MapInfo, MapStats, ModUtil, BeatmapDecoder, ModRelax } from "@rian8337/osu-base";
import {
    DroidDifficultyCalculator,
    DroidPerformanceCalculator,
    OsuDifficultyCalculator,
    OsuPerformanceCalculator
} from "@rian8337/osu-difficulty-calculator";
import { readFile } from "fs/promises";

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
const speedmultiplier = args[5];
const multiplierValue = parseFloat(speedmultiplier.replace('x', ''));

if (isNaN(mapid) || isNaN(accuracy_args) || isNaN(misses_args) || isNaN(combo)) {
    console.error('One or more provided arguments are not valid numbers.');
    process.exit(1);
}

async function calculatePerformance() {
    try {
        const data = await readFile(`data/beatmaps/${mapid}.osu`, { encoding: "utf-8" });
        const decoder = new BeatmapDecoder().decode(data);

        const hitObjects = decoder.result.hitObjects;
        const totalObjects = hitObjects._circles + hitObjects._sliders + hitObjects._spinners;

        const accuracy = new Accuracy({
            nmiss: misses_args,
            nobjects: totalObjects,
            percent: accuracy_args,
        });

        let nmrating = new OsuDifficultyCalculator(decoder.result)
        .calculate({ 
            mods, 
            stats: new MapStats({ 
                speedMultiplier: multiplierValue, 
                }) 
            });


        let od_rel = -4; 
        
        if (mods.some(mod => mod.acronym === 'PR' || mod.name === 'Precise')) {
            od_rel = 0;
        }
        const calc = {
            speedDifficulty: nmrating.attributes.speedDifficulty,
            mods: nmrating.attributes.mods,
            starRating: nmrating.attributes.starRating,
            maxCombo: nmrating.attributes.maxCombo,
            aimDifficulty: nmrating.attributes.aimDifficulty,
            flashlightDifficulty: 0,
            speedNoteCount: nmrating.attributes.speedNoteCount,
            sliderFactor: nmrating.attributes.sliderFactor,
            approachRate: nmrating.attributes.approachRate,
            overallDifficulty: nmrating.attributes.overallDifficulty+od_rel,
            hitCircleCount: nmrating.attributes.hitCircleCount,
            sliderCount: nmrating.attributes.sliderCount,
            spinnerCount: nmrating.attributes.spinnerCount,
        };

  
        const nmperformance = new OsuPerformanceCalculator(calc).calculate({
            accPercent: accuracy,
            combo: combo,
        });
 
        let pp_return = 0;
        
        let accFactor = 1;
        if (accuracy_args < 100) {
            let c = ((100 - accuracy_args) / 30);
            accFactor = Math.exp(-c); // Use negative exponent to ensure the factor is <= 1
        }
        
        let speedReduction = (nmperformance.speed/nmperformance.total-0.25);
        let speedReductionFactor = Math.exp(-speedReduction);

        // console.log("nmperformance.speed: " + nmperformance.speed);
        // console.log("nmperformance.total: " + nmperformance.total);
        // console.log("speedReductionFactor: " + speedReductionFactor);
        // console.log("bonusReductionFactor: " + accFactor);
        pp_return = nmperformance.total - nmperformance.speed;
        pp_return = pp_return * accFactor * speedReductionFactor ; // Apply the reduction factor directly to pp_return
        console.log(pp_return);
        } catch (err) {
            console.error('Error reading or processing the beatmap file:', err);
            process.exit(1);
        }
        }



calculatePerformance();