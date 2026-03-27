"""
Único punto de contacto con la tabla integraciones-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.repositories.base_repository import check_db_error
from src.utils.app_error import AppError

TABLE = "integraciones-escobar"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def find_by_user(user_id: str) -> list:
    """Devuelve todas las integraciones de un usuario."""
    response = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).order("connected_at", desc=True).execute()
    )
    check_db_error(response, "Error al obtener integraciones")
    return response.data


async def find_by_user_and_tipo(user_id: str, tipo: str) -> dict | None:
    """Devuelve una integración por user_id y tipo, o None."""
    response = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).eq("tipo", tipo).maybe_single().execute()
    )
    check_db_error(response, "Error al obtener integración")
    return response.data


async def upsert(user_id: str, tipo: str, credenciales: dict) -> dict:
    """Crea o actualiza una integración (ON CONFLICT user_id, tipo)."""
    response = (
        get_supabase().table(TABLE)
        .upsert(
            {"user_id": user_id, "tipo": tipo, "credenciales": credenciales,
             "activo": True, "updated_at": _now()},
            on_conflict="user_id,tipo",
        ).execute()
    )
    check_db_error(response, "Error al guardar integración")
    return response.data[0]


async def toggle_activo(user_id: str, tipo: str) -> dict:
    """Invierte activo de una integración. Lanza INTEGRACION_NOT_FOUND (404)."""
    actual = await find_by_user_and_tipo(user_id, tipo)
    if not actual:
        raise AppError("Integración no encontrada", "INTEGRACION_NOT_FOUND", 404)
    response = (
        get_supabase().table(TABLE)
        .update({"activo": not actual["activo"], "updated_at": _now()})
        .eq("user_id", user_id).eq("tipo", tipo).execute()
    )
    check_db_error(response, "Error al cambiar estado de integración")
    return response.data[0]


async def eliminar(user_id: str, tipo: str) -> None:
    """Elimina permanentemente una integración. Lanza INTEGRACION_NOT_FOUND (404)."""
    response = (
        get_supabase().table(TABLE).delete()
        .eq("user_id", user_id).eq("tipo", tipo).execute()
    )
    check_db_error(response, "Error al eliminar integración")
    if not response.data:
        raise AppError("Integración no encontrada", "INTEGRACION_NOT_FOUND", 404)
