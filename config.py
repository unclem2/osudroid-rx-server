import os
from dotenv import load_dotenv

load_dotenv(override=True)
## MAIN ##
server_name = 'o!d relax server'  # yes
port = os.getenv('PORT')  # server port
host = os.getenv('SERVER_HOST')
## CRON ##
# 1 = 1 Minute
cron_delay = 10  # used for updating user stats, if your server is big, you might want to set it to 60 or higher to
# make sure your server doesnt die lol

## RANKING ##
#- GLOBAL -#
# enable to use pp system
pp = True
pp_leaderboard = True  # Shows pp instead of score and sort by pp
# used for beatmap info, unused if pp is disabled
osu_key = os.getenv('OSU_KEY', '')
db_url = os.getenv('DATABASE_URL', '')
discord_hook = os.getenv('DISCORD', '')
#- MAINTENACE -#
disable_submit = False  # Does what it says and shows a message to user when trying to play submit a play.
