"""
Único punto de contacto con la tabla conversaciones-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("conversacionRepository")

TABLE = "conversaciones-escobar"


async def find_by_user(user_id: str, limite: int = 20) -> list:
    """
    Obtiene conversaciones de un usuario, ordenadas por actividad reciente.

    Args:
        user_id: UUID del usuario.
        limite: Cantidad máxima de resultados.

    Returns:
        Lista de conversaciones con id, titulo, created_at, updated_at.
    """
    response = (
        get_supabase()
        .table(TABLE)
        .select("id, titulo, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(limite)
        .execute()
    )
    if hasattr(response, "error") and response.error:
        logger.error("Error en find_by_user: %s", response.error)
        raise AppError("Error al obtener conversaciones", "DB_ERROR", 500)
    return response.data


async def find_by_id(conv_id: str, user_id: str) -> dict | None:
    """
    Busca una conversación por ID verificando ownership.

    Args:
        conv_id: UUID de la conversación.
        user_id: UUID del usuario (ownership check).

    Returns:
        dict con la conversación o None si no existe.
    """
    response = (
        get_supabase()
        .table(TABLE)
        .select("*")
        .eq("id", conv_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if hasattr(response, "error") and response.error:
        logger.error("Error en find_by_id conversacion: %s", response.error)
        raise AppError("Error al obtener conversación", "DB_ERROR", 500)
    return response.data


async def create(user_id: str) -> dict:
    """
    Crea una conversación vacía para un usuario.

    Args:
        user_id: UUID del usuario.

    Returns:
        dict con la conversación creada (messages: []).
    """
    response = (
        get_supabase()
        .table(TABLE)
        .insert({"user_id": user_id, "titulo": None, "messages": []})
        .execute()
    )
    if hasattr(response, "error") and response.error:
        logger.error("Error en create conversacion: %s", response.error)
        raise AppError("Error al crear conversación", "DB_ERROR", 500)
    return response.data[0]


async def update_messages(conv_id: str, messages: list, user_id: str) -> dict:
    """
    Reemplaza el array de mensajes de una conversación.

    Args:
        conv_id: UUID de la conversación.
        messages: Array completo actualizado.
        user_id: UUID del usuario (ownership check).

    Returns:
        dict con la conversación actualizada.

    Raises:
        AppError: CONVERSACION_NOT_FOUND si no existe o no pertenece al usuario.
    """
    now = datetime.now(timezone.utc).isoformat()
    response = (
        get_supabase()
        .table(TABLE)
        .update({"messages": messages, "updated_at": now})
        .eq("id", conv_id)
        .eq("user_id", user_id)
        .execute()
    )
    if hasattr(response, "error") and response.error:
        logger.error("Error en update_messages: %s", response.error)
        raise AppError("Error al actualizar conversación", "DB_ERROR", 500)
    if not response.data:
        raise AppError("Conversación no encontrada", "CONVERSACION_NOT_FOUND", 404)
    return response.data[0]


async def update(conv_id: str, user_id: str, campos: dict) -> dict | None:
    """
    Actualiza campos arbitrarios de una conversación verificando ownership.

    Args:
        conv_id: UUID de la conversación.
        user_id: UUID del usuario (ownership check).
        campos: dict con los campos a actualizar.

    Returns:
        dict con la conversación actualizada o None.
    """
    campos["updated_at"] = datetime.now(timezone.utc).isoformat()
    response = (
        get_supabase()
        .table(TABLE)
        .update(campos)
        .eq("id", conv_id)
        .eq("user_id", user_id)
        .execute()
    )
    if hasattr(response, "error") and response.error:
        logger.error("Error en update conversacion: %s", response.error)
        raise AppError("Error al actualizar conversación", "DB_ERROR", 500)
    return response.data[0] if response.data else None
