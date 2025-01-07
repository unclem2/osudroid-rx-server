from quart import Blueprint, make_response
from handlers.response import Success

bp = Blueprint('user_logout', __name__)


@bp.route('/logout.php', methods=['GET'])
async def logout():
    response = await make_response(Success('Logout successful'))
    response.delete_cookie('login_state')
    return response
