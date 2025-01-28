class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def __dict__(self):
        return {"x": self.x, "y": self.y}


class CursorOccurrence:
    def __init__(self, x, y, time, id):
        self.position = Vector(x, y)
        self.time = time
        self.id = id

    @property
    def __dict__(self):
        return {"position": self.position.__dict__, "time": self.time,
                "id": self.id}
