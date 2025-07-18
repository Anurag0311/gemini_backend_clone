from typing import Annotated
from fastapi import Depends

import os
import redis.asyncio as redis


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

# Global Redis client
redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=0,
    decode_responses=True
)


async def get_redis_client() -> redis.Redis:
    return redis_client

RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
