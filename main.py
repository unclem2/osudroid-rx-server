import logging
import time
from contextlib import asynccontextmanager

import coloredlogs
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from socketio import ASGIApp

from handlers.multi import sio
from objects import glob
from objects.player import Player
import handlers
from handlers.response import Failed
import utils
from objects.beatmap import Beatmap
from utils.tasks import TaskManager


async def init_players():
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    if player_ids:
        for player_id in player_ids:
            player = await Player.from_sql(player_id["id"])
            glob.players.add(player)


async def update_player_stats():
    try:
        for player in glob.players:
            await player.update_stats()
    except Exception as err:
        logging.error("Failed to complete task", exc_info=True)


async def update_map_status():
    qualified_maps = await glob.db.fetchall("SELECT * FROM maps WHERE status = 3")
    for qualified_map in qualified_maps if qualified_maps else []:
        map = await Beatmap.from_bid_osuapi(int(qualified_map["id"]))
        if map is None:
            continue
        logging.info("Updated map %d to %s", map.id, map.status)
        await utils.send_webhook(
            title="Updated map",
            content=f"Updated map {map.id} to {map.status}",
            url=glob.config.wl_hook,
            isEmbed=True,
        )


@asynccontextmanager
async def lifespan(app_instance):
    utils.check_folder()
    await glob.db.connect()
    glob.task_manager = TaskManager()
    await init_players()
    glob.task_manager.add_periodic_task(
        update_player_stats, glob.config.cron_delay * 60
    )
    glob.task_manager.add_periodic_task(
        update_map_status, glob.config.cron_delay * 60 * 24
    )
    yield
    await glob.db.close()


templates = Jinja2Templates(directory="templates")

app = FastAPI(lifespan=lifespan, redirect_slashes=False)

app.mount("/static", StaticFiles(directory="static"), name="static")

routes = handlers.load_routers()
for router, prefix in routes:
    app.include_router(router, prefix=prefix)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    logging.debug(f"request {request.method} {request.url.path} took {duration}s")
    return response


@app.exception_handler(500)
async def server_fucked(request: Request, exc: Exception):
    return Failed(f"Server Error: {repr(exc)}")


@app.get("/", include_in_schema=False)
async def index(request: Request):
    players = len(glob.players)
    online = len([_ for _ in glob.players if _.online])
    title = glob.config.server_name
    changelog = glob.config.client_changelog
    version = glob.config.client_version
    download_link = glob.config.client_link

    return templates.TemplateResponse(
        request,
        "main_page.html",
        {
            "players": players,
            "online": online,
            "title": title,
            "changelog": changelog,
            "download_link": download_link,
            "version": version,
        },
    )


def main():
    import uvicorn

    coloredlogs.install(level=logging.DEBUG)

    app_asgi = ASGIApp(sio, app)
    glob.config.host = f"https://{glob.config.domain}"

    uvicorn.run(
        app_asgi,
        host="127.0.0.1",
        port=glob.config.port,
        log_level="debug",
        access_log=True,
    )


if __name__ == "__main__":
    main()
