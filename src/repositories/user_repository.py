"""
Único punto de contacto con la tabla usuarios-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("userRepository")

TABLE = "usuarios-escobar"


async def find_by_email(email: str) -> dict | None:
    """
    Busca un usuario por email.

    Args:
        email: Email del usuario.

    Returns:
        dict con los datos del usuario, o None si no existe.

    Raises:
        AppError: DB_ERROR si falla la query.
    """
    response = get_supabase().table(TABLE).select("*").eq("email", email).maybe_single().execute()

    if hasattr(response, "error") and response.error:
        logger.error("Error en find_by_email: %s", response.error)
        raise AppError("Error al buscar usuario", "DB_ERROR", 500)

    return response.data


async def find_by_id(user_id: str) -> dict | None:
    """
    Busca un usuario por ID.

    Args:
        user_id: UUID del usuario.

    Returns:
        dict con los datos del usuario, o None si no existe.

    Raises:
        AppError: DB_ERROR si falla la query.
    """
    response = get_supabase().table(TABLE).select("*").eq("id", user_id).maybe_single().execute()

    if hasattr(response, "error") and response.error:
        logger.error("Error en find_by_id: %s", response.error)
        raise AppError("Error al buscar usuario", "DB_ERROR", 500)

    return response.data


async def update(user_id: str, campos: dict) -> dict:
    """
    Actualiza campos de un usuario existente.

    Args:
        user_id: UUID del usuario.
        campos: Campos a actualizar.

    Returns:
        dict con el usuario actualizado.

    Raises:
        AppError: USER_NOT_FOUND (404) si no existe.
        AppError: DB_ERROR (500) si falla la query.
    """
    campos["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        get_supabase().table(TABLE)
        .update(campos)
        .eq("id", user_id)
        .execute()
    )

    if hasattr(response, "error") and response.error:
        logger.error("Error en update user: %s", response.error)
        raise AppError("Error al actualizar usuario", "DB_ERROR", 500)

    if not response.data:
        raise AppError("Usuario no encontrado", "USER_NOT_FOUND", 404)

    return response.data[0]
