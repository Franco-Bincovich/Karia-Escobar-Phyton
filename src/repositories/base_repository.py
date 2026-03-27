"""
Helpers compartidos para todos los repositorios.
Evita duplicación de lógica de validación de respuestas de Supabase.
"""

from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("repository")


def check_db_error(response, operation: str) -> None:
    """
    Valida la respuesta de Supabase y lanza DB_ERROR si hay error.

    Args:
        response: Respuesta del SDK de Supabase.
        operation: Descripción de la operación (para log y mensaje de error).

    Raises:
        AppError: DB_ERROR (500) si la respuesta contiene un error.
    """
    if hasattr(response, "error") and response.error:
        logger.error("%s: %s", operation, response.error)
        raise AppError(operation, "DB_ERROR", 500)
