"""
Generación de presentaciones y documentos con Gamma AI.
"""

import httpx

from src.services import integracion_service
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("gamma")

GAMMA_ENDPOINT = "https://api.gamma.app/v1/generate"


async def generar_presentacion(
    user_id: str, titulo: str, contenido: str, formato: str = "presentacion", **_,
) -> dict:
    """
    Genera una presentación usando Gamma AI.
    Requiere integración 'gamma' activa.

    Args:
        titulo: Título principal.
        contenido: Contenido descriptivo.
        formato: presentacion | documento | pagina.

    Returns:
        dict con url y titulo.

    Raises:
        AppError: GAMMA_NOT_CONNECTED | GAMMA_API_ERROR.
    """
    try:
        creds = await integracion_service.get_credenciales(user_id, "gamma")
    except AppError as err:
        if err.code in ("INTEGRACION_NOT_FOUND", "INTEGRACION_INACTIVA"):
            raise AppError(
                "Conectá tu cuenta de Gamma desde Integraciones para generar presentaciones.",
                "GAMMA_NOT_CONNECTED", 400,
            )
        raise

    api_key = creds.get("api_key")
    if not api_key:
        raise AppError("API key de Gamma no encontrada", "GAMMA_NOT_CONNECTED", 400)

    logger.info("Generando presentación Gamma userId=%s titulo=%s formato=%s", user_id, titulo, formato)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                GAMMA_ENDPOINT,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"title": titulo, "content": contenido, "format": formato},
            )
            res.raise_for_status()
            data = res.json()
            return {"url": data.get("url", ""), "titulo": titulo}
    except httpx.HTTPStatusError as e:
        logger.error("Gamma API error: %s", str(e))
        raise AppError(f"Error de Gamma AI: HTTP {e.response.status_code}", "GAMMA_API_ERROR", 502)
    except Exception as e:
        logger.error("Gamma error: %s", str(e))
        raise AppError(f"Error al generar presentación: {e}", "GAMMA_API_ERROR", 500)
