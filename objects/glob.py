import config
from .collections import PlayerList, RoomList
from objects.db import PostgresDB
from utils.tasks import TaskManager

players: PlayerList = PlayerList()
rooms: RoomList = RoomList()
rec_tokens = {}  # temporary solution

cache: dict = {"hashes": {}, "beatmaps": {}, "unsubmitted": []}

db = PostgresDB()

task_manager: TaskManager = None
