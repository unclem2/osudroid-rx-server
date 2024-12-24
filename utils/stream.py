import math
import time
import numpy as np

def calc_radius(map):
    return 54.4 - 4.48 * map.cs

def adjust_beat_length(beat_length, new_bpm):
    current_bpm = new_bpm
    whole = beat_length
    half = whole / 2
    quarter = half / 2
    return current_bpm, whole, half, quarter

def determine(map, beatmap):  # Determine BPM changes
    default_bpm = beatmap["bpm"]["default"]

    for i in map.timing_points:
        point = i
        time = int(float(point.time))
        beatLength = float(point.ms_per_beat)
        if beatLength > 0:
            bpm = str(int(60000 // beatLength))
            if default_bpm["bpm"] == 0:
                default_bpm["time"] = time
                default_bpm["bpm"] = bpm
                default_bpm["beatLength"] = beatLength
            else:
                beatmap["bpm"]["changes"].append(
                    {"time": time, "bpm": bpm, "beatLength": beatLength}
                )
    return beatmap

def calculate_angle(previous_object, current_object, next_object):
    # Используем numpy для быстрого вычисления
    v1 = np.array([current_object["x"] - previous_object["x"],
                   current_object["y"] - previous_object["y"]])
    v2 = np.array([next_object["x"] - current_object["x"],
                   next_object["y"] - current_object["y"]])

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    # Проверяем на нулевые длины векторов
    if norm1 == 0 or norm2 == 0:
        return 180  # Если один из векторов отсутствует

    # Угол через dot-product
    cos_angle = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    angle_degrees = math.degrees(np.arccos(cos_angle))
    return angle_degrees


def calculate_distance(previous_object, current_object):
    return np.linalg.norm([
        current_object["x"] - previous_object["x"],
        current_object["y"] - previous_object["y"]
    ])


def calculate_penalty(previous_object, current_object, next_object, radius):
    penalty = 0.167
    current_angle = current_object['angle']
    prev_angle = previous_object['angle']

    distance_prev = calculate_distance(previous_object, current_object)
    distance_next = calculate_distance(current_object, next_object)
    penalty += 0.2 - 0.2 * (distance_prev / radius)
    # angle penalty
    penalty += 0.2 - 0.2 * (current_angle / 180)
    # delta angle penalty
    delta_angle = prev_angle - current_angle
    penalty += 0.2 - 0.2 * (delta_angle / 180)
    # distance penalty
    penalty += 0.2 - 0.2 * abs(distance_next / radius - distance_prev / radius)
    
    if penalty < 0:
        penalty = 0
    return penalty
    

def get_results(map, beatmap):
    first_object = map.objects[0]
    previous_object = {"time": 0, "x": 0, "y": 0}
    whole = beatmap["bpm"]["default"]["beatLength"]
    half = whole / 2
    quarter = half / 2
    quarter_note_count = 1
    note_start_time = 0
    total_stream_notes = 0
    objects_dict = []

    for i in range(0, len(map.objects)):
        raw_hit_object = map.objects[i]
        if i != len(map.objects) - 1:
            next_raw_hit_object = map.objects[i + 1]
        else:
            next_raw_hit_object = map.objects[i]

        hit_object = {
            "time": int(raw_hit_object.time),
            "x": int(raw_hit_object.pos[0]),
            "y": int(raw_hit_object.pos[1]),
        }
        next_object = {
            "time": int(next_raw_hit_object.time),
            "x": int(next_raw_hit_object.pos[0]),
            "y": int(next_raw_hit_object.pos[1]),
        }
        
        changes = beatmap["bpm"]["changes"]
        for change in changes:
            time_change = change["time"]
            new_beatlength = change["beatLength"]
            new_bpm = change["bpm"]
            if time_change < previous_object["time"]:
                continue
            elif hit_object["time"] >= time_change:

                current_bpm, whole, half, quarter = adjust_beat_length(
                    new_beatlength, new_bpm
                )
                break

        # Determine if quarter length
        if i != first_object:
            time_difference = hit_object["time"] - previous_object["time"]
            hit_object['is_stream'] = False
            hit_object['angle'] = calculate_angle(previous_object, hit_object, next_object)
            hit_object['penalty'] = 0.0001
            if quarter - 2 < time_difference < quarter + 2:  
                hit_object['is_stream'] = True 
                hit_object['penalty'] = calculate_penalty(previous_object, hit_object, next_object, calc_radius(map))
                quarter_note_count += 1
                if note_start_time == 0:
                    note_start_time = hit_object["time"]

            else:
                # Declare if stream
                if 3 < quarter_note_count:
                    total_stream_notes += quarter_note_count
                quarter_note_count = 1
                note_start_time = 0
        objects_dict.append(hit_object)
        previous_object = hit_object

    stream_percentage = 0
    try:
        for obj in objects_dict:
            stream_percentage += obj['penalty']
        stream_percentage = stream_percentage / len(objects_dict) * 100
    except ZeroDivisionError:
        stream_percentage = 0
    return stream_percentage

def check(map):

    beatmap = {
        "bpm": {"default": {"time": 0, "bpm": 0, "beatLength": 0}, "changes": []}
    }
    beatmap = determine(map, beatmap)
    stream_percentage = get_results(map, beatmap)
    if stream_percentage >= 0:
        fin_dict = {
            "stream_percentage": stream_percentage
        }
        return fin_dict
    
    return False

  
