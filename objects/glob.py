import config
from .collections import PlayerList
from objects.db import PostgresDB

players: PlayerList = PlayerList()
rooms = {}

cache: dict = {
  'hashes': {},
  'beatmaps': {},
  'unsubmitted': {}
}

db = PostgresDB()