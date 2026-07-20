from fastapi import Depends, Request
from ossapi import OssapiAsync
from redis import asyncio

from objects.clients.processor import ProcessorClient
from objects.dependencies.config import get_config


def get_redis(request: Request) -> asyncio.Redis:
    return request.app.state.redis


def get_processor(config=Depends(get_config)) -> ProcessorClient:
    return ProcessorClient(config=config)


def get_osu_api_client(request: Request) -> OssapiAsync:
    return request.app.state.osu_api_client
