from quart import Blueprint, request, render_template_string, make_response
from objects import glob
from handlers.response import Success
import html_templates
import utils
import os
from argon2 import PasswordHasher

bp = Blueprint('user_web_login', __name__)

php_file = True

@bp.route('/', methods=['GET', 'POST'])
async def web_login():
    # Check if the login state cookie is present
    login_state = request.cookies.get('login_state')
    if login_state is not None:
        return await render_template_string(html_templates.error_template, 
                                            error_message='Already logged in')

    if request.method == 'POST':
        req = await request.form
        username = req.get('username')
        password = req.get('password')

        if not username or not password:
            return await render_template_string(html_templates.error_template,
                                                error_message='Invalid username or password')

        hashed_password = utils.make_md5(f"{password}taikotaiko")

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
            except BaseException:
                return await render_template_string(html_templates.error_template, error_message='Wrong password')

        response = await make_response(Success('Login successful'))
        response.set_cookie('login_state',
                            f'{username}-{player.id}-{utils.make_md5(f"{username}-{player.id}-{os.getenv("KEY")}")}',
                            max_age=60 * 60 * 24 * 30 * 12)  # Cookie expires in 1 year

        return response

    return await render_template_string(html_templates.web_login_temp)

