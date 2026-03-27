"""
Handler global de errores.
Captura AppError y excepciones no manejadas, devuelve JSON consistente.
Formato: { error: true, message: str, code: str }
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.config.index import settings
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("errorHandler")


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Handler para errores operacionales (AppError)."""
    logger.error("Error operacional code=%s message=%s status=%d", exc.code, exc.message, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message, "code": exc.code},
    )


async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler para errores inesperados — no exponer detalles en producción."""
    logger.error("Error inesperado: %s", str(exc))
    message = str(exc) if settings.NODE_ENV != "production" else "Error interno del servidor"
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": message, "code": "INTERNAL_ERROR"},
    )
