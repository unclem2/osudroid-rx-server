import os
import logging
import copy
import time
import hashlib
from quart import Blueprint, request, send_file, render_template_string
from argon2 import PasswordHasher

from objects import glob
from objects.player import Player
from objects.score import Score, SubmissionStatus
from objects.beatmap import RankedStatus
from handlers.response import Failed, Success, Failure

import utils
import html_templates
ph = PasswordHasher()
bp = Blueprint('cho', __name__)
bp.prefix = '/api/'



## Register / Login
@bp.route('/login.php', methods=['POST'])
async def login():
  params = await request.form

  if 'username' not in params or len(params['username']) == 0:
    return Failed("Invalid username.")

  p = glob.players.get(name=params['username'])

  if not p:
    return Failed("User not found.")
  if params['version'] != '41':
    return Failed("This client is outdated. Check pins")
  ## login shites
  res = (await glob.db.fetch("SELECT password_hash, status FROM users WHERE id = $1", [p.id])) 
  status = res['status']
  pswd_hash = res['password_hash']
  hashes = glob.cache['hashes']

  if pswd_hash in hashes:
    if params['password'] != hashes[pswd_hash]:
      return Failed('Wrong password.')
  else:
    try:
      ph.verify(pswd_hash, params['password'])
    except:
      return Failed('Wrong password.')

    hashes[pswd_hash] = params['password']

  if status != 0:
    return Failed("Banned.")

  # update last ping
  p.last_online = time.time()

  # make uuid if havent
  if not p.uuid:
    p.uuid = utils.make_uuid(p.name)

  # returns long string of shit
  return Success('{id} {uuid} {rank} {rank_by} {acc} {name} {avatar}'.format(
    id = p.id,
    uuid = p.uuid,
    rank = p.stats.rank,
    rank_by = int(p.stats.rank_by),
    acc = p.stats.droid_acc,
    name = p.name,
    avatar = f'https://s.gravatar.com/avatar/{p.email_hash}'
  ))


@bp.route('/register.php', methods=['GET','POST'])
async def register():
  if request.method == 'POST':
    params = await request.form

    for args in ['username', 'password' , 'email']:
      if not params.get(args, None):
        return Failed('Not enough argument.')

    # check username
    if glob.players.get(name=params['username']):
      return Failed("Username already exists.")

    if len(params['username']) < 2:
      return Failed("Username must be longer than 2 characters.")

    pasw = params['password'] + "taikotaiko"
    md5_hash = hashlib.md5()
    md5_hash.update(pasw.encode('utf-8'))
    pasw_hashed = md5_hash.hexdigest()
    
    player_id = await glob.db.execute(
          '''
      INSERT INTO users (
          prefix, username, username_safe, password_hash, device_id, sign, avatar_id, custom_avatar, email, email_hash, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id
      ''',
      [
          None,
          params['username'],
          utils.make_safe(params['username']),
          ph.hash(pasw_hashed),
          "okyeah",
          'NotUsed',
          None,
          None,
          params['email'],
          utils.make_md5(params['email']),
          0
      ]
  )    
    
    # also create stats table
    await glob.db.execute(
        'INSERT INTO stats (id) VALUES ($1)',
        [int(player_id)]
    )
    # create player
    p = await Player.from_sql(player_id)
    glob.players.add(p)

    return Success('Account Created.')
  return await render_template_string(html_templates.registration_form)

## Leaderboard / View Replay Data / View Actual Replay / Upload Replay
@bp.route('/getrank.php', methods=['POST'])
async def leaderboard():
  params = await request.form

  if 'hash' not in params:
    return Failed('No map hash.')

  res = []
  plays = await glob.db.fetchall(
    "SELECT * FROM scores WHERE maphash = $1 AND status = 2 ORDER BY {order_by} DESC".format(
        order_by='pp' if glob.config.pp_leaderboard else 'score'
    ),
    [params['hash']]
  )
  for play in plays:
    player = glob.players.get(id=int(play['playerid']))

    res += ['{play_id} {name} {score} {combo} {rank} {mods} {acc} {gravatar_hash}'.format(
      play_id = play['id'],
      name = player.name,
      score = int(play['pp']) if glob.config.pp_leaderboard else play['score'],
      combo = play['combo'],
      rank = play['rank'],
      mods = play['mods'],
      acc = int(play['acc']*1000),
      gravatar_hash = player.email_hash # use gravatar
    )]

  return Success('\n'.join(res))


@bp.route('gettop.php', methods=['POST'])
async def view_score():
  params = await request.form

  play = await glob.db.fetch("SELECT * FROM scores WHERE id = $1", [int(params['playID'])])
  if play:
    
    return Success('{mods} {score} {combo} {rank} {hitgeki} {hit300} {hitkatsu} {hit100} {hit50} {hitmiss} {acc} {date}'.format(
      mods = play['mods'],
      score = int(play['pp']) if glob.config.pp_leaderboard else play['score'],
      combo = play['combo'],
      rank = play['rank'],
      hitgeki = play['hitgeki'],
      hit300 = play['hit300'],
      hitkatsu = play['hitkatsu'],
      hit100 = play['hit100'],
      hit50 = play['hit50'],
      hitmiss = play['hitmiss'],
      
      acc = int(play['acc']*1000),
      date = play['date']
    ))

  return Failed('Score not found.')



@bp.route('/upload/<string:replay_path>', methods=['GET'])
async def view_replay(replay_path: str):
  path = f'data/replays/{replay_path}' # already have .odr

  if not os.path.isfile(path):
    return Failed('Replay not found.')

  return await send_file(path)

@bp.route('/upload.php', methods=['POST'])
async def upload_replay():
    # Use await with request.files and request.form for asynchronous access
  files = await request.files
  form = await request.form

    # Correctly access the file and replayID
  file = files.get('uploadedfile')
  replay_id = form.get('replayID')

  path = f'data/replays/{replay_id}.odr' # doesnt have .odr
  raw_replay = file.read()
  

  if raw_replay[:2] != b'PK':
    return Failed('Fuck off lol.')

  if os.path.isfile(path):
    return Failed('File already exists.')

  with open(path, 'wb') as file:
    file.write(raw_replay)

  return Success('Replay uploaded.')

## Play Submit - god i hate this part

@bp.route('/submit.php', methods=['POST'])
async def submit_play():
  params = await request.form

  if 'userID' not in params:
    return Failed('Not enough argument.')

  p = glob.players.get(id=int(params['userID']))
  p.last_online = time.time()

  if not p:
    return Failed('Player not found, report to server admin.')

  if 'ssid' in params:
    if params['ssid'] != p.uuid:
      return Failed('Mismatch UUID, please relogin.')

  if glob.config.disable_submit:
    return Failed('Score submission is disable right now.')

  if (map_hash := params.get('hash', None)):
    logging.info(f'Changed {p} playing to {map_hash}')
    p.stats.playing = map_hash
    return Success(1, p.id)

  elif (play_data := params.get('data')):
    s = await Score.from_submission(play_data)

    if not s:
      return Failed('Failed to read score data.')

    if s.status == SubmissionStatus.BEST:
      # if this score is better change old play status to 1
      await glob.db.execute('UPDATE scores SET status = 1 WHERE status = 2 AND mapHash = $1 AND playerID = $2', [s.map_hash, s.player.id])
    if s.map_hash == None:
      return Failed('Server cannot find your recent play, maybe it restarted?')
    elif not s.player:
      return Failed('Player not found, report to server admin.')
    elif not s.bmap:
      # Map does not exists, most likely its a shit map.
      # Returns current stats
      return Success(s.player.stats.droid_submit_stats)
    elif s.bmap.status == RankedStatus.Pending:
      # User can remove this themselves, I'm just following gulag's osuSubmitModularSelector.
      return Success(s.player.stats.droid_submit_stats)

    vals = [s.status, s.map_hash, s.player.id, s.score, s.max_combo, s.grade, s.acc, s.h300, s.hgeki, s.h100, s.hkatsu, s.h50, s.hmiss, s.mods, s.pp, s.bmap.id, s.date]
    s.id = await glob.db.execute('''
        INSERT INTO scores (status, mapHash, playerID, score, combo, rank, acc, hit300, hitgeki, hit100, hitkatsu, hit50, hitmiss, mods, pp, mapid, date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
    ''', vals)
    upload_replay = False
    if s.status == SubmissionStatus.BEST:
      upload_replay = True

    ## Update stats
    stats = s.player.stats

    stats.plays += 1
    stats.tscore = s.score

    if s.status == SubmissionStatus.BEST and s.bmap.gives_reward:
      additive = s.score

      if s.prev_best:
        additive -= s.prev_best.score

      stats.rscore += additive
      

    ## Update Ranked Score stats to db
    await glob.db.execute(
      'UPDATE stats SET rscore = $1, tscore = $2, plays = $3 WHERE id = $4',
      [stats.rscore, stats.tscore, stats.plays, s.player.id])

    ## Update stats one more time - i know this is retarded cuz we're already doing it above but im basing it from the old code so
    await s.player.update_stats()

    return Success('{rank} {rank_by} {acc} {map_rank} {score_id}'.format(
      rank = int(stats.rank),
      rank_by = int(stats.rank_by),
      acc = stats.droid_acc,
      map_rank = s.rank,
      score_id = s.id if upload_replay else ""
    ))

  return Failed('Huh?') # Client wasnt supposed to get here.



