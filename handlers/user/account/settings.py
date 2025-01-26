from quart import Blueprint, request, render_template
from objects import glob
import os
import utils
from werkzeug.utils import secure_filename
from argon2 import PasswordHasher


bp = Blueprint("user_settings", __name__)


@bp.route("/")
async def settings():
    return await render_template("account/settings.jinja")
