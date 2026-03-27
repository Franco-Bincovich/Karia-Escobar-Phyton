"""
Flujo OAuth2 de Google: inicio de autorización y callback.
"""

import asyncio
import time

from jose import jwt, JWTError
from fastapi.responses import RedirectResponse

from src.config.index import settings
from src.config.integraciones import SCOPES_POR_SERVICIO, SERVICIOS_VALIDOS
from src.integrations.google_oauth_factory import crear_oauth_client
from src.services import integracion_service
from src.utils.app_error import AppError
from src.utils.crypto import cifrar, descifrar
from src.utils.logger import get_logger

logger = get_logger("oauthController")

_ALG = "HS256"


async def conectar_google_controller(datos: dict, user: dict) -> dict:
    """
    POST /api/integraciones/google/auth
    Devuelve {url} para redirigir al OAuth de Google.
    """
    raw = datos.get("servicios", "")
    servicios = [s.strip() for s in raw.split(",") if s.strip() in SERVICIOS_VALIDOS]
    if not servicios:
        raise AppError(
            f"Seleccioná al menos un servicio: {', '.join(SERVICIOS_VALIDOS)}",
            "SERVICIOS_REQUERIDOS", 400,
        )

    client_id = (datos.get("clientId") or "").strip()
    client_secret = (datos.get("clientSecret") or "").strip()
    scopes = [s for svc in servicios for s in SCOPES_POR_SERVICIO[svc]]

    flow = crear_oauth_client(client_id or None, client_secret or None, scopes)

    state_payload: dict = {"userId": user["userId"], "servicios": servicios}
    if client_id:
        state_payload["cid"] = cifrar(client_id)
    if client_secret:
        state_payload["csc"] = cifrar(client_secret)

    state_payload["exp"] = int(time.time()) + 600  # 10 min
    estado = jwt.encode(state_payload, settings.OAUTH_STATE_SECRET, algorithm=_ALG)

    url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=estado)
    logger.info("Iniciando OAuth Google userId=%s servicios=%s", user["userId"], servicios)
    return {"url": url}


async def callback_google_controller(code: str, state: str, error: str | None = None):
    """
    GET /api/integraciones/google/callback
    Intercambia code por tokens, guarda para cada servicio, redirige al frontend.
    """
    if error:
        raise AppError(f"Google rechazó la autorización: {error}", "GOOGLE_AUTH_DENIED", 400)

    try:
        payload = jwt.decode(state, settings.OAUTH_STATE_SECRET, algorithms=[_ALG])
        user_id = payload["userId"]
        servicios = payload.get("servicios", SERVICIOS_VALIDOS)
        client_id = descifrar(payload["cid"]) if payload.get("cid") else None
        client_secret = descifrar(payload["csc"]) if payload.get("csc") else None
    except (JWTError, KeyError):
        raise AppError("State OAuth inválido o expirado", "OAUTH_STATE_INVALID", 400)

    scopes = [s for svc in servicios for s in SCOPES_POR_SERVICIO[svc]]
    flow = crear_oauth_client(client_id, client_secret, scopes)
    flow.fetch_token(code=code)

    creds = flow.credentials
    tokens = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }

    await asyncio.gather(*[
        integracion_service.guardar_token_google(
            user_id, svc, tokens, client_id or "", client_secret or "",
        )
        for svc in servicios
    ])

    logger.info("OAuth Google completado userId=%s", user_id)
    frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
    return RedirectResponse(url=f"{frontend_url}?connected=google")
