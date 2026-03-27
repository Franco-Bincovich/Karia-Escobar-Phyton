"""
Cliente Redis singleton (lazy) con graceful degradation.
Si Redis no está disponible, devuelve None y el sistema sigue funcionando
con fallback a rate limiting en memoria.
"""

import redis.asyncio as aioredis

from src.config.index import settings
from src.utils.logger import get_logger

logger = get_logger("redisClient")

_client: aioredis.Redis | None = None
_initialized: bool = False


async def get_redis() -> aioredis.Redis | None:
    """
    Devuelve el cliente Redis async singleton.
    Si Redis no está disponible, loguea warning y devuelve None.

    Returns:
        redis.asyncio.Redis si la conexión es exitosa, None si no.
    """
    global _client, _initialized

    if _initialized:
        return _client

    _initialized = True

    if not settings.REDIS_URL:
        logger.warning("REDIS_URL no configurada, rate limiting degradado a memoria")
        return None

    try:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        await _client.ping()
        logger.info("Redis conectado en %s", settings.REDIS_URL)
        return _client
    except Exception as err:
        logger.warning("Redis no disponible (%s), rate limiting degradado a memoria", str(err))
        _client = None
        return None
