"""
Refresco de tokens OAuth2 de Google con deduplicación de requests concurrentes.
"""

import asyncio

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from src.config.index import settings
from src.config.integraciones import TIPOS_GOOGLE
from src.utils.logger import get_logger

logger = get_logger("googleTokenRefresh")

# Deduplicación: evita refreshes concurrentes para el mismo userId
_refresh_in_flight: dict[str, asyncio.Task] = {}


async def refresh_and_persist(
    user_id: str, refresh_token: str, client_id: str, client_secret: str,
) -> Credentials:
    """
    Refresca el access_token y persiste los nuevos tokens en todos los servicios Google.

    Args:
        user_id: UUID del usuario.
        refresh_token: Refresh token vigente.
        client_id: OAuth client ID.
        client_secret: OAuth client secret.

    Returns:
        google.oauth2.credentials.Credentials actualizado.
    """
    if user_id in _refresh_in_flight:
        return await _refresh_in_flight[user_id]

    async def _do_refresh():
        try:
            creds = Credentials(
                token=None, refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id, client_secret=client_secret,
            )
            creds.refresh(Request())

            # Import lazy para evitar circular
            from src.services import integracion_service
            tokens = {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token or refresh_token,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
            }
            for servicio in TIPOS_GOOGLE:
                try:
                    await integracion_service.guardar_token_google(
                        user_id, servicio, tokens, client_id, client_secret,
                    )
                except Exception as e:
                    logger.warning("No se pudo persistir token %s: %s", servicio, str(e))
            return creds
        finally:
            _refresh_in_flight.pop(user_id, None)

    task = asyncio.create_task(_do_refresh())
    _refresh_in_flight[user_id] = task
    return await task
