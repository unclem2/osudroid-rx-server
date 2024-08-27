import os
import logging
import copy
import time
import hashlib
from quart import Blueprint, request, send_file, render_template_string, make_response
from argon2 import PasswordHasher
import aiohttp
from objects import glob
from objects.player import Player
from objects.score import Score, SubmissionStatus
from objects.beatmap import RankedStatus, Beatmap
from handlers.response import Failed, Success, Failure
import pathlib
import utils
import html_templates
import requests
from werkzeug.utils import secure_filename

bp = Blueprint('user', __name__)
bp.prefix = '/user/'

@bp.route('/avatar/<int:uid>.png')
async def avatar(uid: int):
    
    avatar = pathlib.Path(f'./data/avatar/{uid}.png')

    return await send_file(avatar, mimetype='image/png')

@bp.route('/leaderboard.php')
async def leaderboard():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/leaderboard") as resp:
            data = await resp.json()
            return await render_template_string(html_templates.leaderboard_temp, leaderboard=data)
        
@bp.route('/profile.php')
async def profile():
    params = request.args
    if 'login_state' not in request.cookies:
        pass
    if 'login_state' in request.cookies:
        id = int(request.cookies['login_state'].split('-')[1])
    if 'id' in params:
        id = int(params['id'])

    p = glob.players.get(id=id)
    if not p:
        return Failed('Player not found')
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/get_scores?id={p.id}") as resp:
            try:
                recent_scores = await resp.json()
                for score in recent_scores:
                    bmap = await Beatmap.from_md5_sql(score['maphash'])
                    score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
                    score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            except:
                recent_scores = []
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/top_scores?id={p.id}") as resp:
            try:
                top_scores = await resp.json()
                for score in top_scores:
                    bmap = await Beatmap.from_md5_sql(score['maphash'])                
                    score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
                    score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            except:
                top_scores = []
    return await render_template_string(html_templates.profile_temp, player=p, recent_scores=recent_scores, top_scores=top_scores)

@bp.route('/set_avatar.php', methods=['GET', 'POST'])
async def set_avatar():
    # Check if the authentication cookie is present
    auth_cookie = request.cookies.get('login_state')
    if not auth_cookie:
        return Failure(reason="Not authenticated")

    # Validate the cookie format and extract username and player ID
    try:
        username, player_id = auth_cookie.split('-')
        player_id = int(player_id)
    except ValueError:
        return Failure("Invalid authentication cookie")

    if request.method == 'POST':
        # Await the request.files to ensure it's not a coroutine
        files = await request.files
        form = await request.form

        # Check if the avatar file is part of the request
        if 'avatar' not in files:
            return Failure("No file part")

        file = files.get('avatar')
        if file.filename == '':
            return Failure("No selected file")

        # Retrieve player object
        p = glob.players.get(name=username)
        if not p or p.id != player_id:
            return Failure("Player not found or ID mismatch")

        # Validate and save the avatar file
        if file and allowed_file(file.filename):
            file.filename = f"{p.id}.png"
            filename = secure_filename(file.filename)
            file_path = os.path.join('data/avatar', filename)
            await file.save(file_path)

            return Success("Avatar updated successfully")
        else:
            return Failure("Invalid file type")

    return await render_template_string(html_templates.set_avatar_temp)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/web_login.php', methods=['GET', 'POST'])
async def web_login():
    # Check if the login state cookie is present
    login_state = request.cookies.get('login_state')
    if login_state is not None:
        return Success('Already logged in as ' + login_state.split('-')[0])

    if request.method == 'POST':
        req = await request.form
        username = req.get('username')
        password = req.get('password')

        if not username or not password:
            return Failed('Username and password are required')

        # Append salt to the password and hash it using MD5
        salted_password = f"{password}taikotaiko"
        md5_hash = hashlib.md5()
        md5_hash.update(salted_password.encode('utf-8'))
        hashed_password = md5_hash.hexdigest()

        # Retrieve player information
        ph = PasswordHasher()
        player = glob.players.get(name=username)
        if not player:
            return Failed('Player not found')

        # Fetch password hash and status from the database
        res = await glob.db.fetch("SELECT password_hash, status FROM users WHERE id = $1", [player.id])
        if not res:
            return Failed('Player not found in database')

        stored_password_hash = res['password_hash']
        status = res['status']
        cached_hashes = glob.cache['hashes']

        # Verify the password
        if stored_password_hash in cached_hashes:
            if hashed_password != cached_hashes[stored_password_hash]:
                return Failed('Wrong password.')
        else:
            try:
                ph.verify(stored_password_hash, hashed_password)
            except:
                return Failed('Wrong password.')

        # Create a response object and set a cookie with the login state
        response = await make_response(Success('Login successful'))
        response.set_cookie('login_state', f'{username}-{player.id}', max_age=60*60*24*30*12)  # Cookie expires in 1 day
        
        return response

    # Render the login template for GET requests
    return await render_template_string(html_templates.web_login_temp)