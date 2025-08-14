from pydantic_core import PydanticCustomError
from quart import Blueprint, request
from objects import glob
from .models.player import PlayerModel
from objects.player import Player
from handlers.response import ApiResponse
from pydantic import BaseModel, model_validator
from typing import Optional
from quart_schema import validate_response, validate_querystring, RequestSchemaValidationError


bp = Blueprint("get_user", __name__)

class UserRequest(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_args(cls, values):
        if not values.get("id") and not values.get("username"):
            raise PydanticCustomError("validation_error", "Either id or username must be provided.")
        if values.get("username") is not None and len(values["username"]) < 2:
            raise PydanticCustomError("validation_error", "Invalid username.")
        return values


@bp.route("/")
@validate_querystring(UserRequest)
@validate_response(ApiResponse[PlayerModel], 200)
async def get_user(query_args: UserRequest) -> ApiResponse[PlayerModel]:
    """
    Get user.
    """
    if query_args.id is not None:
        player = glob.players.get(id=query_args.id)
    else:
        player: Player = glob.players.get(username=query_args.username)

    if not player:
        return ApiResponse.not_found("User not found")

    return ApiResponse.ok(PlayerModel(**player.as_json))

@bp.errorhandler(RequestSchemaValidationError)
async def handle_validation_error(error: RequestSchemaValidationError):
    """
    Handle validation errors for request schema.
    """
    error_message = error.validation_error.errors()[0]["msg"]
    return ApiResponse.bad_request(str(error_message))