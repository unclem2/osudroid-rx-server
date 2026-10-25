from typing import AsyncGenerator

from fastapi import Depends, Request
from ossapi import OssapiAsync
from redis import asyncio

from objects.clients.processor import ProcessorClient
from objects.dependencies.config import get_config


def get_redis(request: Request) -> asyncio.Redis:
    return request.app.state.redis


async def get_processor(config=Depends(get_config)) -> AsyncGenerator[ProcessorClient, None]:
    client = ProcessorClient(config=config)
    try:
        yield client
    finally:
        await client.close()


def get_osu_api_client(request: Request) -> OssapiAsync:
    return request.app.state.osu_api_client
