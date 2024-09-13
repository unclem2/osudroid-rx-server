import config
from .collections import PlayerList, RoomList

players: PlayerList = PlayerList()
rooms = {}

cache: dict = {
  'hashes': {},
  'beatmaps': {},
  'unsubmitted': {}
}
