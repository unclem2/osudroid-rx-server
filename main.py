import os
import logging
import asyncio
import coloredlogs

from quart import Quart, jsonify, render_template, send_from_directory, g, request
from socketio import ASGIApp
from quart_schema import QuartSchema

# Other imports
from handlers.multi import sio
from objects import glob
from objects.player import Player
import handlers
from handlers.response import Failed
import utils
from objects.beatmap import Beatmap

import hypercorn
import hypercorn.asyncio
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware
import time
from utils.tasks import TaskManager


async def init_players():
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
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
        logging.info("Updated map %d to %s", map.id, map.status)
        await utils.send_webhook(
            title="Updated map",
            content=f"Updated map {map.id} to {map.status}",
            url=glob.config.wl_hook,
            isEmbed=True,
        )
        await asyncio.sleep(5)


def make_app():
    quart_app = Quart(__name__)
    QuartSchema(quart_app)
    routes = handlers.load_blueprints()
    for route in routes:
        quart_app.register_blueprint(route, url_prefix=route.prefix)
    return quart_app


app = make_app()


def handle_ex(loop, context):
    logging.warning("SSL error ignored: ")


@app.before_serving
async def init():
    utils.check_folder()
    await glob.db.connect()
    glob.task_manager = TaskManager()
    await init_players()
    glob.task_manager.add_periodic_task(
        update_player_stats, glob.config.cron_delay * 60
    )
    glob.task_manager.add_periodic_task(
        update_map_status, glob.config.cron_delay * 3600
    )
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_ex)


@app.after_serving
async def close():
    """
    Close the database connection after the server is closed.
    """
    await glob.db.close()


@app.before_request
async def before_request():
    g.start_time = time.perf_counter()
    pass


@app.after_request
async def after_request(response):
    duration = time.perf_counter() - g.start_time
    logging.debug(f"request {request.method} {request.path} took {duration}s")
    return response


@app.errorhandler(500)
async def server_fucked(err):
    return Failed(f"Server Error: {repr(err)}")


# Serving static folder first
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


@app.route("/")
async def index():
    players = len(glob.players)
    online = len([_ for _ in glob.players if _.online])
    title = glob.config.server_name
    # if main page kills everything then theres huge chance that something is
    # wrong with certificates(good way to check if certs valid and/or placed correctly)
    # works fine without certificates

    changelog = glob.config.client_changelog
    version = glob.config.client_version
    download_link = glob.config.client_link

    return await render_template(
        "main_page.jinja",
        players=players,
        online=online,
        title=title,
        changelog=changelog,
        download_link=download_link,
        version=version,
    )


def main():
    hypercorn_config = hypercorn.Config()
    coloredlogs.install(level=logging.INFO)

    if os.path.exists(f"/etc/letsencrypt/live/{glob.config.domain}"):
        redirected_app = HTTPToHTTPSRedirectMiddleware(app, host=glob.config.domain)
        app_asgi = ASGIApp(sio, redirected_app)
        hypercorn_config.bind = ["0.0.0.0:443"]
        hypercorn_config.keyfile = os.path.join(
            f"/etc/letsencrypt//live/{glob.config.domain}/privkey.pem"
        )
        hypercorn_config.certfile = os.path.join(
            f"/etc/letsencrypt/live/{glob.config.domain}/fullchain.pem"
        )
        glob.config.host = f"https://{glob.config.domain}:443"
    else:
        app_asgi = ASGIApp(sio, app)
        hypercorn_config.bind = [f"{glob.config.ip}:{glob.config.port}"]
        glob.config.host = f"http://{glob.config.ip}:{glob.config.port}"
        hypercorn_config.debug = True
        hypercorn_config.loglevel = "DEBUG"
        hypercorn_config.accesslog = "-"
        hypercorn_config.errorlog = "-"
    asyncio.run(hypercorn.asyncio.serve(app_asgi, hypercorn_config))


if __name__ == "__main__":
    main()
