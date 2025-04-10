from quart import Blueprint, make_response, render_template
from handlers.response import Success

bp = Blueprint("user_logout", __name__)

php_file = True


@bp.route("/", methods=["GET"])
async def logout():
    response = await render_template(
        "success.jinja", success_message=Success("Logout successful")
    )
    response = await make_response(response)
    response.delete_cookie("login_state")
    return response
