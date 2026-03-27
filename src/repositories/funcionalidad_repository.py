"""
Único punto de contacto con la tabla funcionalidades-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.repositories.base_repository import check_db_error
from src.utils.app_error import AppError

TABLE = "funcionalidades-escobar"


async def find_active_by_user(user_id: str) -> list:
    """Devuelve funcionalidades activas del usuario, ordenadas por created_at asc."""
    response = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).eq("activo", True)
        .order("created_at", desc=False).execute()
    )
    check_db_error(response, "Error al obtener funcionalidades")
    return response.data


async def find_all_by_user(user_id: str) -> list:
    """Devuelve todas las funcionalidades del usuario (activas e inactivas)."""
    response = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False).execute()
    )
    check_db_error(response, "Error al obtener funcionalidades")
    return response.data


async def create(user_id: str, datos: dict) -> dict:
    """Crea una nueva funcionalidad para el usuario."""
    response = get_supabase().table(TABLE).insert({"user_id": user_id, **datos}).execute()
    check_db_error(response, "Error al crear funcionalidad")
    return response.data[0]


async def update(func_id: str, user_id: str, campos: dict) -> dict:
    """Actualiza campos verificando ownership. Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    campos["updated_at"] = datetime.now(timezone.utc).isoformat()
    response = (
        get_supabase().table(TABLE).update(campos)
        .eq("id", func_id).eq("user_id", user_id).execute()
    )
    check_db_error(response, "Error al actualizar funcionalidad")
    if not response.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
    return response.data[0]


async def toggle_activo(func_id: str, user_id: str) -> dict:
    """Invierte activo (true->false, false->true). Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    response = (
        get_supabase().table(TABLE).select("activo")
        .eq("id", func_id).eq("user_id", user_id)
        .maybe_single().execute()
    )
    check_db_error(response, "Error al obtener funcionalidad")
    if not response.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
    return await update(func_id, user_id, {"activo": not response.data["activo"]})


async def eliminar(func_id: str, user_id: str) -> None:
    """Elimina permanentemente verificando ownership. Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    response = (
        get_supabase().table(TABLE).delete()
        .eq("id", func_id).eq("user_id", user_id).execute()
    )
    check_db_error(response, "Error al eliminar funcionalidad")
    if not response.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
