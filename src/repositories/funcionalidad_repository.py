"""
Único punto de contacto con la tabla funcionalidades-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("funcionalidadRepository")

TABLE = "funcionalidades-escobar"


def _check(response, msg: str):
    """Valida respuesta de Supabase y lanza DB_ERROR si hay error."""
    if hasattr(response, "error") and response.error:
        logger.error("%s: %s", msg, response.error)
        raise AppError(msg, "DB_ERROR", 500)


async def find_active_by_user(user_id: str) -> list:
    """Devuelve funcionalidades activas del usuario, ordenadas por created_at asc."""
    resp = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).eq("activo", True)
        .order("created_at", desc=False).execute()
    )
    _check(resp, "Error al obtener funcionalidades")
    return resp.data


async def find_all_by_user(user_id: str) -> list:
    """Devuelve todas las funcionalidades del usuario (activas e inactivas)."""
    resp = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False).execute()
    )
    _check(resp, "Error al obtener funcionalidades")
    return resp.data


async def create(user_id: str, datos: dict) -> dict:
    """Crea una nueva funcionalidad para el usuario."""
    resp = get_supabase().table(TABLE).insert({"user_id": user_id, **datos}).execute()
    _check(resp, "Error al crear funcionalidad")
    return resp.data[0]


async def update(func_id: str, user_id: str, campos: dict) -> dict:
    """Actualiza campos verificando ownership. Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    campos["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = (
        get_supabase().table(TABLE).update(campos)
        .eq("id", func_id).eq("user_id", user_id).execute()
    )
    _check(resp, "Error al actualizar funcionalidad")
    if not resp.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
    return resp.data[0]


async def toggle_activo(func_id: str, user_id: str) -> dict:
    """Invierte activo (true→false, false→true). Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    resp = (
        get_supabase().table(TABLE).select("activo")
        .eq("id", func_id).eq("user_id", user_id)
        .maybe_single().execute()
    )
    _check(resp, "Error al obtener funcionalidad")
    if not resp.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
    return await update(func_id, user_id, {"activo": not resp.data["activo"]})


async def eliminar(func_id: str, user_id: str) -> None:
    """Elimina permanentemente verificando ownership. Lanza FUNCIONALIDAD_NOT_FOUND (404)."""
    resp = (
        get_supabase().table(TABLE).delete()
        .eq("id", func_id).eq("user_id", user_id).execute()
    )
    _check(resp, "Error al eliminar funcionalidad")
    if not resp.data:
        raise AppError("Funcionalidad no encontrada", "FUNCIONALIDAD_NOT_FOUND", 404)
