import enum


class MovementType(enum.Enum):
    DOWN = 0
    MOVE = 1
    UP = 2

    @property
    def __dict__(self):
        return self.value
