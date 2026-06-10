import os
from dotenv import load_dotenv
import json

load_dotenv(override=True)

# Main server configuration
server_name = "osudroid!relax"
server_description = "Server that aims to be a relax mod only version of osu!droid, for those people that like to play RX and wish it were ranked."
port = int(os.getenv("SERVER_PORT", 8080))
ip = os.getenv("SERVER_IP")
domain = os.getenv("SERVER_DOMAIN")
host = ""  # Internal use only

# Client configuration
online_version = 9
client_link = "https://github.com/unclem2/odrx-client/releases/download/1.16.3/osu.droid-1.16.3.250829.-debug-2025-08-29.apk"
client_version = "1.16.3(250829)"
client_version_code = 1756470004
client_changelog = "spectator support"
banner_url = "https://discord.gg/Ub4nXasaHd"

# State toggles
legacy = False  # Enable to use legacy submit system
maintenance = False
disable_submit = False  # Disables play submissions and notifies users

# Cron job settings
cron_delay = 10  # Delay (in minutes) for updating user stats

# Ranking system configuration
pp = True  # Enable pp system
pp_leaderboard = True  # Show and sort leaderboard by pp
max_pp_value = 10000  # Max pp value for a play

# External service keys and URLs
osu_key = os.getenv("OSU_KEY", "")
db_url = os.getenv("DATABASE_URL", "")
submit_hook = os.getenv("SUBMIT_DISCORD", "")
wl_hook = os.getenv("WL_DISCORD", "")
wl_key = os.getenv("WL_KEY", "")
login_key = os.getenv("LOGIN_KEY", "")


# maybe will be used later
# not finished

# class ConfigValue():
#     def __init__(self, value=None, is_locked=False):
#         self.__value = value
#         self.__is_locked = is_locked

#     @property
#     def value(self):
#         return self.__value

#     @value.setter
#     def value(self, new_value):
#         if not self.__is_locked or self.__value == None:
#             self.__value = new_value
#         else:
#             raise ValueError("This config value is locked and cannot be changed.")

# class Config:
#     def __init__(self):
#         pass

#     def __setattr__(self, name, value):
#         if hasattr(self, name):
#             current_value = getattr(self, name)
#             current_value.value = value
#         else:
#             super().__setattr__(name, ConfigValue(value))

#     def __getattribute__(self, name):
#         if hasattr(self, name):
#             current_value = getattr(self, name)
#             return current_value.value
#         raise AttributeError(f"Config has no attribute '{name}'")

#     def load(self):
#         with open("config.json", "r") as f:
#             data = json.load(f)
#             for key, value in data.items():
#                 setattr(self, key, ConfigValue(value.get("value"), value.get("is_locked", False)))
