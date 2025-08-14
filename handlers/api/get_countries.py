from quart import Blueprint, jsonify
import utils
from handlers.response import ApiResponse
from quart_schema import validate_response
from pydantic import BaseModel
from typing import List

bp = Blueprint("get_countries", __name__)


@bp.route("/")
@validate_response(ApiResponse[List[str]], 200)
async def get_countries():
    """
    Get a list of all countries.
    """
    countries = await utils.get_countries()
    return ApiResponse.ok([country for country in countries])
