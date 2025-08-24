import json
import os
import time


def write_event(
    id: int, event: str, direction: int, data: dict | str, receiver=None, sender=None
):
    """
    Write an event to a JSON file for a specific room.

    Args:
        id (int): The ID of the room.
        event (str): The event name.
        direction (int): The direction of the event (0 for out, 1 for in).
        data (dict): The data associated with the event.
        to (str, optional): The recipient of the event. Defaults to None.
    """
    if event == "spectatorData":
        print("Skipping spectatorData event logging")
        return
    with open(f"data/rooms/{id}.jsonl", "a") as f:
        dump_data = {
            "event": event,
            "data": data,
            "direction": "out" if direction == 0 else "in",
            "timestamp": int(time.time()),
            "to": receiver,
            "from": sender,
        }
        json.dump(dump_data, f, ensure_ascii=False)
        f.write("\n")


def read_room_log(id: int) -> list:
    with open(f"data/rooms/{id}.jsonl", "r") as f:
        room_data = []
        for line in f.readlines():
            try:
                room_data.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return room_data


def get_id() -> str:
    """
    Get the next available room ID.

    Returns:
        int: The next available room ID.
    """

    rooms = os.listdir("data/rooms")
    if len(rooms) == 0:
        return "1"
    else:
        ids = [int(room.split(".")[0]) for room in rooms]
        return str(max(ids) + 1)
