"""
Dependency de FastAPI para verificación de JWT.
Extrae el Bearer token del header Authorization y devuelve el usuario autenticado.
"""

from fastapi import Depends, HTTPException, Request

from src.services.auth_service import verificar_token
from src.utils.logger import get_logger

logger = get_logger("auth")


async def get_current_user(request: Request) -> dict:
    """
    Dependency que verifica el JWT en el header Authorization.

    Returns:
        dict con userId, email y rol del usuario autenticado.

    Raises:
        HTTPException 401: si no hay token, está vencido o es inválido.
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": True, "message": "Token requerido", "code": "TOKEN_REQUIRED"},
        )

    token = auth_header[7:]  # quitar "Bearer "

    try:
        user = await verificar_token(token)
        logger.info("Token verificado userId=%s", user["userId"])
        return user
    except Exception as exc:
        code = getattr(exc, "code", "TOKEN_INVALID")
        message = getattr(exc, "message", "Token inválido")
        raise HTTPException(
            status_code=401,
            detail={"error": True, "message": message, "code": code},
        )
