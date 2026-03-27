"""
Crea un cliente OAuth2 autenticado para un usuario.
Refresca tokens expirados delegando a google_token_refresh.
"""

import time

from google.oauth2.credentials import Credentials

from src.config.index import settings
from src.integrations.google_token_refresh import refresh_and_persist
from src.services import integracion_service
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("googleClient")


async def get_google_client(user_id: str, tipo: str) -> Credentials:
    """
    Devuelve credenciales OAuth2 autenticadas y listas para usar.
    Refresca el access_token automáticamente si expiró.

    Args:
        user_id: UUID del usuario.
        tipo: 'gmail', 'drive' o 'calendar'.

    Returns:
        google.oauth2.credentials.Credentials.

    Raises:
        AppError: GOOGLE_NOT_CONNECTED | GOOGLE_CREDENTIALS_MISSING | GOOGLE_TOKEN_EXPIRED.
    """
    try:
        creds = await integracion_service.get_credenciales(user_id, tipo)
    except AppError as err:
        if err.code in ("INTEGRACION_NOT_FOUND", "INTEGRACION_INACTIVA"):
            raise AppError(
                f"Google {tipo} no está conectado. Conectá tu cuenta desde Integraciones.",
                "GOOGLE_NOT_CONNECTED", 400,
            )
        raise

    cid = creds.get("client_id") or settings.GOOGLE_CLIENT_ID
    csecret = creds.get("client_secret") or settings.GOOGLE_CLIENT_SECRET
    if not cid or not csecret:
        raise AppError(
            "Configurá las credenciales de Google Cloud Console en Integraciones.",
            "GOOGLE_CREDENTIALS_MISSING", 400,
        )

    expiry = int(creds["expiry"]) if creds.get("expiry") else None
    expirado = expiry and (time.time() * 1000) >= (expiry - 60_000)

    if expirado and creds.get("refresh_token"):
        try:
            return await refresh_and_persist(user_id, creds["refresh_token"], cid, csecret)
        except Exception:
            raise AppError(
                "La sesión de Google expiró. Volvé a conectar tu cuenta desde Integraciones.",
                "GOOGLE_TOKEN_EXPIRED", 401,
            )

    return Credentials(
        token=creds.get("access_token"), refresh_token=creds.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token", client_id=cid, client_secret=csecret,
    )
