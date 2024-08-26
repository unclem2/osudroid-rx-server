import os
import logging
import copy
import time
import hashlib
from quart import Blueprint, request, send_file, render_template_string
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
    if 'id' not in params:
        return Failed('ID is required')
    if not params['id'].isdecimal():
        return Failed('Invalid ID')
    p = glob.players.get(id=int(params['id']))
    if not p:
        return Failed('Player not found')
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/get_scores?id={p.id}") as resp:
            recent_scores = await resp.json()
            for score in recent_scores:
                bmap = await Beatmap.from_md5_sql(score['maphash'])
                score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
                score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/top_scores?id={p.id}") as resp:
            top_scores = await resp.json()
            for score in top_scores:
                bmap = await Beatmap.from_md5_sql(score['maphash'])                
                score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
                score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"

    return await render_template_string(html_templates.profile_temp, player=p, recent_scores=recent_scores, top_scores=top_scores)

@bp.route('/set_avatar.php', methods=['GET', 'POST'])
async def set_avatar():
    if request.method == 'POST':
        # Await the request.files to ensure it's not a coroutine
        files = await request.files
        form = await request.form

        # Check if the avatar file is part of the request
        if 'avatar' not in files:
            return Failure(reason="No file part")

        file = files.get('avatar')
        if file.filename == '':
            return Failure(reason="No selected file")

        # Collect login data
        md5_hash = hashlib.md5()

        username = form.get('username')
        password = f"{form.get('password')}taikotaiko"
        md5_hash.update(password.encode('utf-8'))
        password = md5_hash.hexdigest()
        
        if not username or not password:
            return Failure(reason="Username and password are required")

        # Authenticate user
        data = {
            'username': username,
            'password': password,
            'version': '2'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"http://{glob.config.host}:{glob.config.port}/api/login.php", data=data) as resp:
                resp_text = await resp.text()
                print(resp_text)
                if "FAILED" in resp_text:
                    return Failure("Invalid username or password")

        # Retrieve player object
        p = glob.players.get(name=username)
        if not p:
            return Failure("Player not found")

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