"""
Lógica de negocio para funcionalidades del agente.
build_system_prompt es el contrato principal con agent.py.
"""

import re
import unicodedata

from src.repositories import funcionalidad_repository as func_repo
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("funcionalidadService")

# Patrones que indican intentos de prompt injection o jailbreak.
_I = re.IGNORECASE
BLOCKLIST_PROMPT = [
    # --- Patrones del JS original (25 únicos) ---
    re.compile(r"ignor[aá]", _I), re.compile(r"ignore", _I),
    re.compile(r"override", _I), re.compile(r"instrucciones anteriores", _I),
    re.compile(r"previous instructions", _I), re.compile(r"jailbreak", _I),
    re.compile(r"system.?prompt anterior", _I), re.compile(r"forget your instructions", _I),
    re.compile(r"nueva personalidad", _I), re.compile(r"act as", _I),
    re.compile(r"\bDAN\b"), re.compile(r"pretend", _I),
    re.compile(r"disregard", _I), re.compile(r"simulate", _I),
    re.compile(r"roleplay", _I), re.compile(r"from now on", _I),
    re.compile(r"new persona", _I), re.compile(r"forget everything", _I),
    re.compile(r"ignore all", _I), re.compile(r"bypass", _I),
    re.compile(r"act[uú]a como", _I), re.compile(r"fing[ií] que", _I),
    re.compile(r"olvid[aá] todo", _I), re.compile(r"ignor[aá] todo", _I),
    re.compile(r"sin restricciones", _I),
    # --- Patrones adicionales para cobertura 35+ ---
    re.compile(r"do anything now", _I), re.compile(r"ignore previous", _I),
    re.compile(r"you are now", _I), re.compile(r"ahora sos", _I),
    re.compile(r"no rules", _I), re.compile(r"sin reglas", _I),
    re.compile(r"unrestricted", _I), re.compile(r"modo desarrollador", _I),
    re.compile(r"developer mode", _I), re.compile(r"reset your", _I),
    re.compile(r"reinici[aá] tu", _I), re.compile(r"cambi[aá] de rol", _I),
]

_FUNC_BASE = {
    "nombre": "Análisis de documentos",
    "descripcion": "Analiza documentos PDF, Word y Excel subidos al chat.",
    "system_prompt": (
        "Podés analizar documentos que el usuario suba al chat. "
        "Usá la herramienta analizar_documento para procesar PDFs, Word y Excel."
    ),
}


def _normalizar_prompt(text: str) -> str:
    """Normaliza NFC, remueve zero-width chars y colapsa espacios."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)
    return re.sub(r"\s+", " ", text).strip()


async def listar(user_id: str) -> list:
    """Lista todas las funcionalidades. Auto-crea 'Análisis de documentos' si falta."""
    rows = await func_repo.find_all_by_user(user_id)
    if not any(f["nombre"] == _FUNC_BASE["nombre"] for f in rows):
        base = await func_repo.create(user_id, _FUNC_BASE)
        rows.insert(0, base)
    return rows


async def crear(user_id: str, datos: dict) -> dict:
    """Crea una funcionalidad validando system_prompt contra la blocklist."""
    sp = datos.get("system_prompt", "")
    if not sp or not sp.strip():
        raise AppError("El system prompt no puede estar vacío", "SYSTEM_PROMPT_REQUERIDO", 400)

    normalizado = _normalizar_prompt(sp)
    for patron in BLOCKLIST_PROMPT:
        if patron.search(normalizado):
            logger.warning("Prompt injection bloqueado userId=%s patron=%s", user_id, patron.pattern)
            raise AppError(
                "El system prompt contiene contenido no permitido", "SYSTEM_PROMPT_INVALIDO", 400
            )

    row = await func_repo.create(user_id, {
        "nombre": datos["nombre"].strip(),
        "descripcion": (datos.get("descripcion") or "").strip() or None,
        "system_prompt": sp.strip(),
    })
    logger.info("Funcionalidad creada userId=%s id=%s nombre=%s", user_id, row["id"], row["nombre"])
    return row


async def toggle_activo(func_id: str, user_id: str) -> dict:
    """Alterna activo/inactivo de una funcionalidad."""
    row = await func_repo.toggle_activo(func_id, user_id)
    logger.info("Funcionalidad toggled userId=%s id=%s activo=%s", user_id, func_id, row["activo"])
    return row


async def eliminar(func_id: str, user_id: str) -> None:
    """Elimina permanentemente una funcionalidad."""
    await func_repo.eliminar(func_id, user_id)
    logger.info("Funcionalidad eliminada userId=%s id=%s", user_id, func_id)


async def build_system_prompt(user_id: str) -> str | None:
    """
    Construye el system prompt dinámico combinando funcionalidades activas.
    Devuelve None si no hay funcionalidades — agent.py usa el prompt base como fallback.
    """
    funcionalidades = await func_repo.find_active_by_user(user_id)
    if not funcionalidades:
        return None
    return "\n\n".join(f"=== {f['nombre']} ===\n{f['system_prompt']}" for f in funcionalidades)
