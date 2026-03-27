"""
Lógica de negocio para integraciones de terceros.
Las credenciales se cifran con AES-256-CBC antes de persistir y nunca
se exponen al frontend — solo el agente las consume via get_credenciales().
"""

from src.config.integraciones import TIPOS_API_KEY, TIPOS_GOOGLE
from src.repositories import integracion_repository as int_repo
from src.utils.app_error import AppError
from src.utils.crypto import cifrar, descifrar
from src.utils.logger import get_logger

logger = get_logger("integracionService")


async def listar_integraciones(user_id: str) -> list:
    """Lista integraciones sin exponer credenciales. Auto-crea Anthropic si falta."""
    rows = await int_repo.find_by_user(user_id)
    if not any(r["tipo"] == "anthropic" for r in rows):
        base = await int_repo.upsert(user_id, "anthropic", {})
        rows.insert(0, base)
    return [
        {"id": r["id"], "tipo": r["tipo"], "activo": r["activo"],
         "connected_at": r.get("connected_at"), "updated_at": r.get("updated_at")}
        for r in rows
    ]


async def guardar_api_key(user_id: str, tipo: str, api_key: str) -> None:
    """Guarda una API key cifrada. Tipos válidos: anthropic, openai, perplexity, gamma."""
    if tipo not in TIPOS_API_KEY:
        raise AppError(f"Tipo inválido. Valores permitidos: {', '.join(TIPOS_API_KEY)}", "TIPO_INVALIDO", 400)
    if not api_key or not api_key.strip():
        raise AppError("La API key no puede estar vacía", "API_KEY_INVALIDA", 400)
    await int_repo.upsert(user_id, tipo, {"api_key": cifrar(api_key.strip())})
    logger.info("API key guardada userId=%s tipo=%s", user_id, tipo)


async def guardar_token_google(
    user_id: str, tipo: str, tokens: dict, client_id: str = "", client_secret: str = "",
) -> None:
    """Guarda tokens OAuth de Google cifrados. Tipos: gmail, drive, calendar."""
    if tipo not in TIPOS_GOOGLE:
        raise AppError(f"Tipo inválido. Valores permitidos: {', '.join(TIPOS_GOOGLE)}", "TIPO_INVALIDO", 400)
    at, rt = tokens.get("access_token"), tokens.get("refresh_token")
    if not at or not rt:
        raise AppError("access_token y refresh_token son obligatorios", "TOKENS_INVALIDOS", 400)
    expiry = tokens.get("expiry")
    creds = {
        "access_token": cifrar(at), "refresh_token": cifrar(rt),
        "expiry": cifrar(str(expiry)) if expiry else None,
        "client_id": cifrar(client_id) if client_id else None,
        "client_secret": cifrar(client_secret) if client_secret else None,
    }
    await int_repo.upsert(user_id, tipo, creds)
    logger.info("Token Google guardado userId=%s tipo=%s", user_id, tipo)


async def toggle_activo(user_id: str, tipo: str) -> dict:
    """Alterna activo/inactivo de una integración."""
    row = await int_repo.toggle_activo(user_id, tipo)
    logger.info("Integración toggled userId=%s tipo=%s activo=%s", user_id, tipo, row["activo"])
    return {"activo": row["activo"]}


async def desconectar(user_id: str, tipo: str) -> None:
    """Elimina permanentemente una integración."""
    await int_repo.eliminar(user_id, tipo)
    logger.info("Integración desconectada userId=%s tipo=%s", user_id, tipo)


async def get_credenciales(user_id: str, tipo: str) -> dict:
    """Devuelve credenciales descifradas. USO EXCLUSIVO DEL AGENTE."""
    row = await int_repo.find_by_user_and_tipo(user_id, tipo)
    if not row:
        raise AppError("Integración no encontrada", "INTEGRACION_NOT_FOUND", 404)
    if not row["activo"]:
        raise AppError("La integración está desactivada", "INTEGRACION_INACTIVA", 403)
    return {k: descifrar(v) if v else None for k, v in (row.get("credenciales") or {}).items()}


async def get_integraciones_activas(user_id: str) -> list[str]:
    """Devuelve nombres de las integraciones activas. Ej: ['gmail', 'calendar']."""
    rows = await int_repo.find_by_user(user_id)
    return [r["tipo"] for r in rows if r["activo"]]
