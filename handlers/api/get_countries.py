from quart import Blueprint, jsonify
import utils

bp = Blueprint("get_countries", __name__)


@bp.route("/")
async def get_countries():
    countries = await utils.get_countries()
    return jsonify(countries)
