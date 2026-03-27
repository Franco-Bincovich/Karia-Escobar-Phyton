"""
Rate limiting con Redis (persistente) y fallback a memoria (degradado).
Usa INCR + EXPIRE en Redis para sliding window por key.
Si Redis no está disponible, usa dict en memoria como fallback.
"""

import time

from src.integrations.redis_client import get_redis
from src.utils.logger import get_logger

logger = get_logger("rateLimiter")

# Fallback en memoria: {key: {count, expires_at}}
_memory_store: dict[str, dict] = {}
_MAX_MEMORY_KEYS = 1000


def _cleanup_expired() -> None:
    """Elimina entries expiradas del store en memoria. Limita a _MAX_MEMORY_KEYS."""
    now = time.time()
    expired = [k for k, v in _memory_store.items() if now > v["expires_at"]]
    for k in expired:
        del _memory_store[k]

    # Si aún supera el límite, eliminar las más antiguas
    if len(_memory_store) > _MAX_MEMORY_KEYS:
        sorted_keys = sorted(_memory_store, key=lambda k: _memory_store[k]["expires_at"])
        for k in sorted_keys[:len(_memory_store) - _MAX_MEMORY_KEYS]:
            del _memory_store[k]


def _memory_check(key: str, max_requests: int, window_seconds: int) -> bool:
    """Fallback en memoria cuando Redis no está disponible."""
    _cleanup_expired()
    now = time.time()
    entry = _memory_store.get(key)

    if not entry or now > entry["expires_at"]:
        _memory_store[key] = {"count": 1, "expires_at": now + window_seconds}
        return True

    if entry["count"] >= max_requests:
        return False

    entry["count"] += 1
    return True


async def rate_limit_by_key(key: str, max_requests: int, window_seconds: int) -> bool:
    """
    Verifica si un request está permitido bajo el rate limit.

    Usa Redis si está disponible (INCR + EXPIRE sliding window).
    Si Redis no está disponible, usa fallback a dict en memoria.

    Args:
        key: Identificador único del rate limit (ej: "chat:userId", "login:email").
        max_requests: Cantidad máxima de requests permitidos en la ventana.
        window_seconds: Duración de la ventana en segundos.

    Returns:
        True si el request está permitido, False si se superó el límite.
    """
    redis = await get_redis()

    if not redis:
        return _memory_check(key, max_requests, window_seconds)

    try:
        redis_key = f"ratelimit:{key}"
        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, window_seconds)
        return count <= max_requests
    except Exception as err:
        logger.warning("Redis error en rate_limit, fallback a memoria: %s", str(err))
        return _memory_check(key, max_requests, window_seconds)
