"""
Fábrica del cliente OAuth2 de Google.
Integración pura — sin lógica HTTP.
"""

from google_auth_oauthlib.flow import Flow

from src.config.index import settings
from src.config.integraciones import SCOPES_POR_SERVICIO
from src.utils.app_error import AppError


def crear_oauth_client(
    client_id: str | None = None,
    client_secret: str | None = None,
    scopes: list[str] | None = None,
) -> Flow:
    """
    Crea un Flow OAuth2 de Google.

    Args:
        client_id: Client ID (cae a config si None).
        client_secret: Client Secret (cae a config si None).
        scopes: Lista de scopes OAuth2.

    Returns:
        google_auth_oauthlib.flow.Flow configurado.

    Raises:
        AppError: GOOGLE_CREDENTIALS_MISSING si faltan credenciales.
    """
    cid = client_id or settings.GOOGLE_CLIENT_ID
    csecret = client_secret or settings.GOOGLE_CLIENT_SECRET

    if not cid or not csecret:
        raise AppError(
            "Configurá tus credenciales de Google Cloud Console en la sección Integraciones",
            "GOOGLE_CREDENTIALS_MISSING",
            400,
        )

    client_config = {
        "web": {
            "client_id": cid,
            "client_secret": csecret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=scopes or [],
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
