import logging
import redis
import json
import utils
from .player import Player

class BaseCollection:
    name: str = "BaseCollection"
    attrs: list = []

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

    def __len__(self):
        return self.redis_client.scard(self.name)

    def __iter__(self):
        for item in self.redis_client.smembers(self.name):
            yield Player(**json.loads(item.decode('utf-8')))

    def __repr__(self):
        return f"<{self.name}|Items: {len(self)}>"

    def add(self, o: object):
        o_json = json.dumps(o.to_dict())
        if self.redis_client.sismember(self.name, o_json):
            return logging.info(f"Already added {o} into {self.name}")

        self.redis_client.sadd(self.name, o_json)
        logging.info(f"Added {o} into {self.name}")

    def fix_attr(self, attr: str, val: str):
        """Override in subclasses if needed."""
        return attr, val

    def get(self, **kwargs):
        for attr in self.attrs:
            if val := kwargs.get(attr, None):
                break
        else:
            raise Exception(f"Failed to get object from {self.name}: kwargs - {kwargs}")

        attr, val = self.fix_attr(attr, val)

        for item in self.redis_client.smembers(self.name):
            obj_data = json.loads(item.decode('utf-8'))
            obj = Player(**obj_data)
            if getattr(obj, attr) == val:
                return obj


    def remove(self, o: object):
        o_json = json.dumps(o.to_dict())
        if self.redis_client.srem(self.name, o_json):
            logging.info(f"Removed {o} from {self.name}")
        else:
            logging.warning(f"Attempted to remove {o} from {self.name}, but it was not found.")


class PlayerList(BaseCollection):
    name = "PlayerList"
    attrs = ["id", "name"]

    def fix_attr(self, attr: str, val: str):
        if attr == "name":
            attr = "name_safe"
            val = utils.make_safe(val)

        return attr, val