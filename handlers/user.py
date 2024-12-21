import os
import dotenv
import time
import hashlib
from quart import Blueprint, request, send_file, render_template_string, make_response
from argon2 import PasswordHasher
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import Success
import pathlib
import html_templates
from werkzeug.utils import secure_filename
from objects.mods import Mods

dotenv.load_dotenv()

bp = Blueprint('user', __name__)
bp.prefix = '/user/'



def get_md5_hash(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    hash = md5_hash.hexdigest()
    return hash

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_md5(string, hash):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    hashed_string =  md5_hash.hexdigest()
    if hashed_string == hash:
        return True
    return False


@bp.route('/avatar/<int:uid>.png')
async def avatar(uid: int):
    avatar = pathlib.Path(f'./data/avatar/{uid}.png')

    return await send_file(avatar, mimetype='image/png')

@bp.route('/leaderboard.php')
async def leaderboard():
    players_stats = await glob.db.fetchall(
        'SELECT stats.id, stats.rank, stats.pp, stats.plays, users.username '
        'FROM stats '
        'INNER JOIN users ON stats.id = users.id ORDER BY stats.pp DESC'
    )

    return await render_template_string(html_templates.leaderboard_temp, leaderboard=players_stats)

@bp.route('/profile.php')
async def profile():
    params = request.args
    id = None
    if 'login_state' not in request.cookies:
        pass
    if 'login_state' in request.cookies:
        id = int(request.cookies['login_state'].split('-')[1])
    if 'id' in params:
        id = int(params['id'])

    if id is None:
        return await render_template_string(html_templates.error_template, error_message='No player ID provided')
    p = glob.players.get(id=id)
    if not p:
        return await render_template_string(html_templates.error_template, error_message='Player not found')
    
    try:
        recent_scores = await glob.db.fetchall(
        'SELECT id, status, "maphash", score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 '
        'ORDER BY id DESC LIMIT $2',
        [p.id, 50]
        )
        for score in recent_scores:
            bmap = await Beatmap.from_md5_sql(score['maphash'])
            score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
            score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            score['acc'] = f"{score['acc']:.2f}%"
            score['pp'] = f"{score['pp']:.2f}" 
            score['mods'] = f"{Mods(score['mods']).convert_std}"
 
    except:
        recent_scores = []
    try:
        top_scores = await glob.db.fetchall(
        'SELECT id, status, maphash, score, combo, rank, acc, "hit300", "hitgeki", '
        '"hit100", "hitkatsu", "hit50", "hitmiss", mods, pp, date FROM scores WHERE "playerid" = $1 AND "status" = 2 AND maphash IN (SELECT md5 FROM maps WHERE status IN (1, 4, 5))'
        'ORDER BY pp DESC',
        [id]
        )
        for score in top_scores:
            bmap = await Beatmap.from_md5_sql(score['maphash'])
            score['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(score['date'] / 1000))
            score['map'] = f"{bmap.artist} - {bmap.title} [{bmap.version}]"
            score['acc'] = f"{score['acc']:.2f}%"
            score['pp'] = f"{score['pp']:.2f}"
            score['mods'] = f"{Mods(score['mods']).convert_std}" 
    except:
        top_scores = []
    return await render_template_string(html_templates.profile_temp, player=p, recent_scores=recent_scores,
                                        top_scores=top_scores)


@bp.route('/set_avatar.php', methods=['GET', 'POST'])
async def set_avatar():
    # Check if the authentication cookie is present
    auth_cookie = request.cookies.get('login_state')
    if not auth_cookie:
        return await render_template_string(html_templates.error_template, error_message='Not logged in')

    # Validate the cookie format and extract username and player ID
    try:
        username, player_id, hash = auth_cookie.split('-')
        if check_md5(f"{username}-{player_id}-{os.getenv("KEY")}", hash) == False:
            return await render_template_string(html_templates.error_template, error_message='Invalid login state')
        player_id = int(player_id)
    except ValueError:
        return await render_template_string(html_templates.error_template, error_message='Invalid login state')

    if request.method == 'POST':
        files = await request.files

        # Check if the avatar file is part of the request
        if 'avatar' not in files:
            return await render_template_string(html_templates.error_template, error_message='No avatar file provided')

        file = files.get('avatar')
        if file.filename == '':
            return await render_template_string(html_templates.error_template, error_message='No selected file')

        # Retrieve player object
        p = glob.players.get(name=username)
        if not p or p.id != player_id:
            return await render_template_string(html_templates.error_template, error_message='Player not found')

        # Validate and save the avatar file
        if file and allowed_file(file.filename):
            file.filename = f"{p.id}.png"
            filename = secure_filename(file.filename)
            file_path = os.path.join('data/avatar', filename)
            await file.save(file_path)

            return await render_template_string(html_templates.success_template,
                                                success_message='Avatar uploaded successfully')
        else:
            return await render_template_string(html_templates.error_template, error_message='Invalid file format')

    return await render_template_string(html_templates.set_avatar_temp)




@bp.route('/web_login.php', methods=['GET', 'POST'])
async def web_login():
    # Check if the login state cookie is present
    login_state = request.cookies.get('login_state')
    if login_state is not None:
        return await render_template_string(html_templates.error_template, error_message='Already logged in')

    if request.method == 'POST':
        req = await request.form
        username = req.get('username')
        password = req.get('password')

        if not username or not password:
            return await render_template_string(html_templates.error_template,
                                                error_message='Invalid username or password')

        hashed_password = get_md5_hash(f"{password}taikotaiko")

        # Retrieve player information
        ph = PasswordHasher()
        player = glob.players.get(name=username)
        if not player:
            return await render_template_string(html_templates.error_template, error_message='Player not found')

        # Fetch password hash and status from the database
        res = await glob.db.fetch("SELECT password_hash, status FROM users WHERE id = $1", [player.id])
        if not res:
            return await render_template_string(html_templates.error_template, error_message='Player not found')

        stored_password_hash = res['password_hash']
        cached_hashes = glob.cache['hashes']

        # Verify the password using ph
        if stored_password_hash in cached_hashes:
            if hashed_password != cached_hashes[stored_password_hash]:
                return await render_template_string(html_templates.error_template, error_message='Wrong password')
        else:
            try:
                ph.verify(stored_password_hash, hashed_password)
            except:
                return await render_template_string(html_templates.error_template, error_message='Wrong password')

        response = await make_response(Success('Login successful'))
        response.set_cookie('login_state', f'{username}-{player.id}-{get_md5_hash(f"{username}-{player.id}-{os.getenv("KEY")}")}',
                            max_age=60 * 60 * 24 * 30 * 12)  # Cookie expires in 1 year

        return response

    return await render_template_string(html_templates.web_login_temp)

@bp.route('/change_password.php', methods=['GET', 'POST'])
async def change_password():
    
    login_state = request.cookies.get('login_state')
    if login_state is None:
        return await render_template_string(html_templates.error_template, error_message='Not logged in')


    if request.method == 'POST':
        req = await request.form
        username, player_id, hash = login_state.split('-')
        if check_md5(f"{username}-{player_id}-{os.getenv("KEY")}", hash) == False:
            return await render_template_string(html_templates.error_template, error_message='Invalid login state')
        old_password = req.get('old_password')
        new_password = req.get('new_password')

        if not old_password or not new_password:
            return await render_template_string(html_templates.error_template,
                                                error_message='Invalid old or new password')

        hashed_old_password = get_md5_hash(f"{old_password}taikotaiko")
        hashed_new_password = get_md5_hash(f"{new_password}taikotaiko")

        ph = PasswordHasher()
        
        player = glob.players.get(id=int(player_id))
        if not player or player.id != int(player_id):
            return await render_template_string(html_templates.error_template, error_message='Player not found')

        res = await glob.db.fetch("SELECT password_hash, status FROM users WHERE id = $1", [player.id])
        if not res:
            return await render_template_string(html_templates.error_template, error_message='Player not found')

        stored_password_hash = res['password_hash']

        try:
            ph.verify(stored_password_hash, hashed_old_password)
        except:
            return await render_template_string(html_templates.error_template, error_message='Wrong password')
        new_password_hash = ph.hash(hashed_new_password)
        await glob.db.execute("UPDATE users SET password_hash = $1 WHERE id = $2", [new_password_hash, player.id])
        return await render_template_string(html_templates.success_template, success_message='Password changed successfully')
    return await render_template_string(html_templates.change_password_template)

@bp.route('/logout.php', methods=['GET'])
async def logout():
    response = await make_response(Success('Logout successful'))
    response.delete_cookie('login_state')
    return response
