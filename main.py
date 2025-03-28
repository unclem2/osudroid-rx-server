import os
import logging
import asyncio
import coloredlogs

from quart import Quart, jsonify, render_template, send_from_directory
from socketio import ASGIApp

# Other imports
from handlers.multi import sio
from objects import glob
from objects.player import Player
import handlers
from handlers.response import Failed
import utils
from objects.beatmap import Beatmap

import hypercorn
import hypercorn.logging
import hypercorn.run

import hypercorn.asyncio
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware



async def init_players():
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    for player_id in player_ids:
        player = await Player.from_sql(player_id["id"])
        glob.players.add(player)


async def update_player_stats():
    while True:
        try:
            for player in glob.players:
                await player.update_stats()
        except Exception as err:
            logging.error("Failed to complete task", exc_info=True)
 
        try:
            await asyncio.sleep(glob.config.cron_delay * 60)
        except Exception as err:
            logging.error("Failed to complete task", exc_info=True)



async def update_map_status():
    while True:
        qualified_maps = await glob.db.fetchall("SELECT * FROM maps WHERE status = 3")
        for qualified_map in qualified_maps:
            map = await Beatmap.from_bid_osuapi(int(qualified_map["id"]))
            logging.info("Updated map %d to %s", map.id, map.status)
            await utils.send_webhook(
                title="Updated map",
                content=f"Updated map {map.id} to {map.status}",
                url=glob.config.discord_hook,
                isEmbed=True,
            )
            await asyncio.sleep(5)
        try:
            await asyncio.sleep(glob.config.cron_delay * 3600)
        except Exception as err:
            logging.error("Failed to complete task: %r", err)


def make_app():
    quart_app = Quart(__name__)
    routes = handlers.load_blueprints()
    for route in routes:
        quart_app.register_blueprint(route, url_prefix=route.prefix)
    return quart_app


app = make_app()

def handle_ex(loop, context):
    logging.warning("SSL error ignored: " )


@app.before_serving
async def init():
    utils.check_folder()
    await glob.db.connect()
    await init_players()
    asyncio.create_task(update_player_stats())
    asyncio.create_task(update_map_status())
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_ex)


@app.after_serving
async def close():
    """
    Close the database connection after the server is closed.
    """
    await glob.db.close()


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
    try:
        asyncio.run(hypercorn.asyncio.serve(app_asgi, hypercorn_config))
    except Exception as e:
        logging.warning("SSL error ignored: %s", e)
    except TimeoutError as e:
        logging.warning("SSL error ignored: %s", e)


if __name__ == "__main__":
    main()
