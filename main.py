import logging
import time
from contextlib import asynccontextmanager

import coloredlogs
import redis.asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ossapi import OssapiAsync

import handlers
import utils
from config import Config
from handlers.response import Failed
from objects.db import engine, init
from tasks import init_player_compose
from utils.tasks import TaskManager

config = Config()


@asynccontextmanager
async def lifespan(app_instance):
    utils.check_folder()
    app_instance.state.task_manager = TaskManager()
    await init(engine)
    func, dep = await init_player_compose(app_instance)

    app_instance.state.task_manager.add_task(func, dep)

    # app_instance.state.task_manager.add_periodic_task(
    #     update_map_status, config.cron_delay * 60 * 24
    # )
    yield


templates = Jinja2Templates(directory="templates")

app = FastAPI(lifespan=lifespan, redirect_slashes=False)
r = redis.asyncio.Redis(host="localhost", port=6379, decode_responses=True)
osu_api_client = OssapiAsync(config.osu_client_id, config.osu_client_secret)


app.mount("/static", StaticFiles(directory="static"), name="static")

routes = handlers.load_routers()
for router, prefix in routes:
    app.include_router(router, prefix=prefix)


app.state.redis = r
app.state.osu_api_client = osu_api_client


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    # logging.debug(await request.form())
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    logging.debug(f"request {request.method} {request.url.path} took {duration}s")
    return response


@app.exception_handler(500)
async def server_fucked(request: Request, exc: Exception):
    return Failed(f"припыли нахуй: {exc!r}")


def main():
    import uvicorn

    coloredlogs.install(level=logging.DEBUG)
    config.host = f"https://{config.domain}"

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.port,
        log_level="info",
        access_log=True,

    )


if __name__ == "__main__":
    main()
