import config
from .collections import PlayerList, RoomList

players: PlayerList = PlayerList()
rooms: RoomList = RoomList()

cache: dict = {
  'hashes': {},
  'beatmaps': {},
  'unsubmitted': {}
}
