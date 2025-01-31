from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
from objects.replay_data.cursoroccurrence import CursorOccurrence
from objects.replay_data.cursoroccurrencegroup import CursorOccurrenceGroup
from objects.replay_data.movementtype import MovementType


class CursorData:
    def __init__(self, values: dict):
        self.occurrence_groups: List[CursorOccurrenceGroup] = []
        down_occurrence: Optional[CursorOccurrence] = None
        move_occurrences: List[CursorOccurrence] = []

        for i in range(values["size"]):
            occurrence = CursorOccurrence(
                time=values["time"][i],
                x=values["x"][i],
                y=values["y"][i],
                id=MovementType(values["id"][i]),
            )

            if occurrence.id == MovementType.DOWN:
                down_occurrence = occurrence
            elif occurrence.id == MovementType.MOVE:
                move_occurrences.append(occurrence)
            elif occurrence.id == MovementType.UP:
                if down_occurrence:
                    self.occurrence_groups.append(
                        CursorOccurrenceGroup(
                            down=down_occurrence,
                            moves=move_occurrences,
                            up=occurrence,
                        )
                    )
                    down_occurrence = None
                move_occurrences = []

        # Handle any remaining occurrences
        if down_occurrence and move_occurrences:
            self.occurrence_groups.append(
                CursorOccurrenceGroup(down=down_occurrence, moves=move_occurrences)
            )

    @property
    def earliest_occurrence_time(self) -> Optional[int]:
        return self.occurrence_groups[0].start_time if self.occurrence_groups else None

    @property
    def latest_occurrence_time(self) -> Optional[int]:
        return self.occurrence_groups[-1].end_time if self.occurrence_groups else None

    @property
    def total_occurrences(self) -> int:
        return sum(
            1 + len(group.moves) + (1 if group.up else 0)
            for group in self.occurrence_groups
        )

    @property
    def all_occurrences(self) -> List[CursorOccurrence]:
        return [
            occurrence
            for group in self.occurrence_groups
            for occurrence in group.all_occurrences
        ]

    @property
    def __dict__(self):
        return {
            "occurrence_groups": [group.__dict__ for group in self.occurrence_groups]
        }
