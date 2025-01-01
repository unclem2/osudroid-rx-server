import config
from .collections import PlayerList
from objects.db import PostgresDB

players: PlayerList = PlayerList()
rooms = {}
rec_tokens = {}  #temporary solution

cache: dict = {
  'hashes': {},
  'beatmaps': {},
  'unsubmitted': {}
}

db = PostgresDB()