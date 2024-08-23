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
import pathlib
import utils
import html_templates

bp = Blueprint('user', __name__)
bp.prefix = '/user/'

@bp.route('/avatar/<int:uid>.png')
async def avatar(uid: int):
    
    avatar = pathlib.Path(f'./data/avatar/{uid}.png')

    return await send_file(avatar, mimetype='image/png')
