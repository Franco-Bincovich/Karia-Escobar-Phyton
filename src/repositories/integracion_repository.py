"""
Único punto de contacto con la tabla integraciones-escobar.
Nunca SQL raw — siempre el SDK de Supabase.
"""

from datetime import datetime, timezone

from src.integrations.supabase_client import get_supabase
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("integracionRepository")

TABLE = "integraciones-escobar"


def _check(response, msg: str):
    """Valida respuesta de Supabase y lanza DB_ERROR si hay error."""
    if hasattr(response, "error") and response.error:
        logger.error("%s: %s", msg, response.error)
        raise AppError(msg, "DB_ERROR", 500)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def find_by_user(user_id: str) -> list:
    """Devuelve todas las integraciones de un usuario."""
    resp = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).order("connected_at", desc=True).execute()
    )
    _check(resp, "Error al obtener integraciones")
    return resp.data


async def find_by_user_and_tipo(user_id: str, tipo: str) -> dict | None:
    """Devuelve una integración por user_id y tipo, o None."""
    resp = (
        get_supabase().table(TABLE).select("*")
        .eq("user_id", user_id).eq("tipo", tipo).maybe_single().execute()
    )
    _check(resp, "Error al obtener integración")
    return resp.data


async def upsert(user_id: str, tipo: str, credenciales: dict) -> dict:
    """Crea o actualiza una integración (ON CONFLICT user_id, tipo)."""
    resp = (
        get_supabase().table(TABLE)
        .upsert(
            {"user_id": user_id, "tipo": tipo, "credenciales": credenciales,
             "activo": True, "updated_at": _now()},
            on_conflict="user_id,tipo",
        ).execute()
    )
    _check(resp, "Error al guardar integración")
    return resp.data[0]


async def toggle_activo(user_id: str, tipo: str) -> dict:
    """Invierte activo de una integración. Lanza INTEGRACION_NOT_FOUND (404)."""
    actual = await find_by_user_and_tipo(user_id, tipo)
    if not actual:
        raise AppError("Integración no encontrada", "INTEGRACION_NOT_FOUND", 404)
    resp = (
        get_supabase().table(TABLE)
        .update({"activo": not actual["activo"], "updated_at": _now()})
        .eq("user_id", user_id).eq("tipo", tipo).execute()
    )
    _check(resp, "Error al cambiar estado de integración")
    return resp.data[0]


async def eliminar(user_id: str, tipo: str) -> None:
    """Elimina permanentemente una integración. Lanza INTEGRACION_NOT_FOUND (404)."""
    resp = (
        get_supabase().table(TABLE).delete()
        .eq("user_id", user_id).eq("tipo", tipo).execute()
    )
    _check(resp, "Error al eliminar integración")
    if not resp.data:
        raise AppError("Integración no encontrada", "INTEGRACION_NOT_FOUND", 404)
