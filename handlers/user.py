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
