from quart import Blueprint, request
from objects import glob
from objects.beatmap import Beatmap
from handlers.response import ApiResponse
from quart_schema import validate_querystring, validate_response, hide
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError
from .models.beatmap import BeatmapModel
from typing import Optional
import utils


bp = Blueprint("wl_add", __name__)


class WhitelistAddRequest(BaseModel):
    key: str
    md5: Optional[str] = None
    bid: Optional[int] = None

    @model_validator(mode="before")
    def validate(cls, values):
        if not values.get("key"):
            raise PydanticCustomError("validation_error", "Key must be provided.")
        if not values.get("md5") and not values.get("bid"):
            raise PydanticCustomError(
                "validation_error", "Either md5 or bid must be provided."
            )
        return values


@bp.route("/", methods=["GET"])
@validate_querystring(WhitelistAddRequest)
@validate_response(ApiResponse[BeatmapModel], 200)
@validate_response(ApiResponse[str], 400)
@validate_response(ApiResponse[str], 403)
async def whitelist_add(query_args: WhitelistAddRequest) -> ApiResponse[BeatmapModel]:
    """
    Add a beatmap to the whitelist.
    """
    if query_args.key != glob.config.wl_key:
        return ApiResponse.forbidden("Invalid key.")
    map = None
    if query_args.md5 is not None:
        map = await Beatmap.from_md5(query_args.md5)
    elif query_args.bid is not None:
        map = await Beatmap.from_bid(query_args.bid)
    if map is None:
        return ApiResponse.not_found(
            "Beatmap not found or missing required attributes."
        )
    glob.task_manager.add_task(map.download())

    # made by operagx
    await utils.send_webhook(
        title=f"☆ {round(map.star, 2)} {map.artist} - {map.title} ({map.creator}) [{map.version}]",
        title_url=f"https://osu.ppy.sh/beatmapsets/{map.set_id}#osu/{map.id}",
        thumbnail=f"https://b.ppy.sh/thumb/{map.set_id}l.jpg",
        content=f"**Map Stats: **\n**CS:** {map.cs} | **AR:** {map.ar} | **OD:** {map.od} | **HP:** {map.hp}",
        footer="Map added to whitelist...",
        url=glob.config.wl_hook,
        isEmbed=True,
    )
    await glob.db.execute("UPDATE maps SET status = 5 WHERE id = $1", [map.id])

    return ApiResponse.ok(BeatmapModel(**map.as_json))
