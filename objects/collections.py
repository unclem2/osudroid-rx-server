import logging
from typing import Optional, TypeVar, Generic
from objects.player import Player
from objects.room.room import Room
import utils

T = TypeVar("T")


class BaseCollection(Generic[T]):
    name: str = "BaseCollection"
    attrs: list[str] = []

    def __init__(self):
        self.storage: list[T] = []

    def __len__(self):
        return len(self.storage)

    def __iter__(self):
        return iter(self.storage)

    def __repr__(self):
        return f"<{self.name}|Items: {len(self)}>"

    def add(self, o: T) -> None:
        if o in self.storage:
            return logging.info(f"Already added {o} into {self.name}")

        self.storage.append(o)
        logging.info(f"Added {o} into {self.name}")

    def fix_attr(self, attr: str, val: str):
        """yes"""
        ...

    def get(self, **kwargs) -> Optional[T]:
        for attr in self.attrs:
            if val := kwargs.get(attr, None):
                break
        else:
            raise Exception(f"Failed to get object from {self.name}: kwargs - {kwargs}")

        attr, val = self.fix_attr(attr, val)

        for x in self.storage:
            if getattr(x, attr) == val:
                return x

    def remove(self, o: object):
        self.storage.remove(o)
        logging.info(f"Removed {o} from {self.name}")


class PlayerList(BaseCollection[Player]):
    name = "PlayerList"
    attrs = ["id", "username"]

    def fix_attr(self, attr: str, val: str):
        if attr == "username":
            attr = "username_safe"
            val = utils.make_safe(val)

        return attr, val


class RoomList(BaseCollection[Room]):
    name = "RoomList"
    attrs = ["id", "name"]

    def fix_attr(self, attr, val):
        return attr, val
