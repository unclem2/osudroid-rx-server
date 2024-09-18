import os
import logging
import asyncio
import coloredlogs
from quart import Quart, render_template_string
import aiohttp
from handlers.multi import sio  # Import the socketio server
from socketio import ASGIApp

# Other imports
from objects import glob
from objects.player import Player
from objects.db import PostgresDB
from handlers import (cho, api, user, multi)
from handlers.response import Failed
import utils
from utils import pp
from objects.beatmap import Beatmap
import html_templates

def make_app():
    app = Quart(__name__)
    glob.db = PostgresDB()

    # Register existing routes
    routes = [cho, api, user, multi]
    for route in routes:
        app.register_blueprint(route, url_prefix=route.prefix)

    return app


app = make_app()

@app.before_serving
async def init_shit():
    utils.check_folder()
    await glob.db.connect()

    # Initialize players
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    for id in player_ids:
        p = await Player.from_sql(id['id'])
        glob.players.add(p)

    async def background_tasks():
        async def update_players_stats():
            for p in glob.players:
                await p.update_stats()

        tasks = [update_players_stats]
        for task in tasks:
            try:
                await task()
            except Exception as err:
                logging.error(f'Failed to complete task: {repr(err)}')

        await asyncio.sleep(glob.config.cron_delay * 60)

    asyncio.ensure_future(background_tasks())

@app.after_serving
async def close_shit():
    await glob.db.close()

@app.errorhandler(500)
async def server_fucked(err):
    return Failed(f'Server Error: {repr(err)}')

@app.route('/')
async def index():
    players = len(glob.players)
    online = len([_ for _ in glob.players if _.online])
    title = 'odrx server'
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{glob.config.host}:{glob.config.port}/api/update.php") as resp:
            update = await resp.json()
            changelog = update['changelog']
            version = update['version_code']
            download_link = update['link']

    return await render_template_string(
        html_templates.main_page, players=players, online=online, title=title, changelog=changelog,
        download_link=download_link, version=version
    )


if __name__ == '__main__':
    coloredlogs.install(level=logging.DEBUG)

    # Wrap the Quart app with Socket.IO's ASGIApp
    app_asgi = ASGIApp(sio, app)

    # Run the app using an ASGI server like hypercorn or uvicorn
    import hypercorn.asyncio

    hypercorn_config = hypercorn.Config()
    hypercorn_config.bind = [f"{glob.config.host}:{glob.config.port}"]
    
    asyncio.run(hypercorn.asyncio.serve(app_asgi, hypercorn_config))
