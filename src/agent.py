"""
Orquestador del agente KarIA Escobar.
Construye contexto dinámico (system prompt, integraciones, timezone) y delega el loop.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.config.system_prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_CONFIGURADOR
from src.integrations.anthropic_client import get_anthropic
from src.services import funcionalidad_service
from src.services import integracion_service
from src.tools import TOOLS
from src.utils.agent_loop import ejecutar_loop
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("agent")

TZ_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


async def ejecutar_agente(mensaje: str, historial: list, user_id: str) -> dict:
    """
    Ejecuta el agente principal con historial y herramientas.

    Args:
        mensaje: Mensaje del usuario.
        historial: Historial de la conversación.
        user_id: ID del usuario autenticado.

    Returns:
        dict con respuesta (str) y mensajes_actualizados (list).

    Raises:
        AppError: CLAUDE_UNAVAILABLE | AGENT_LOOP_ERROR.
    """
    messages = [
        *[{"role": m["role"], "content": m["content"]} for m in historial],
        {"role": "user", "content": mensaje},
    ]

    system_prompt = SYSTEM_PROMPT

    try:
        dinamico = await funcionalidad_service.build_system_prompt(user_id)
        if dinamico:
            system_prompt += "\n\n" + dinamico
    except Exception:
        logger.warning("No se pudo cargar system prompt dinámico, usando fallback userId=%s", user_id)

    ahora = datetime.now(TZ_ARGENTINA).strftime("%d/%m/%Y %H:%M")
    system_prompt += f"\n\nLa fecha y hora actual es: {ahora}"

    try:
        activas = await integracion_service.get_integraciones_activas(user_id)
        if activas:
            nombres = [t.capitalize() for t in activas]
            system_prompt += (
                f"\n\nIntegraciones conectadas del usuario: {', '.join(nombres)}.\n"
                "Podés usar estas integraciones directamente sin pedirle al usuario que las conecte."
            )
    except Exception:
        logger.warning("No se pudieron cargar integraciones activas userId=%s", user_id)

    return await ejecutar_loop(messages, system_prompt, TOOLS, user_id)


async def ejecutar_agente_configurador(mensaje: str, historial: list) -> dict:
    """
    Ejecuta el agente configurador sin herramientas ni persistencia.

    Args:
        mensaje: Mensaje del usuario.
        historial: Historial en memoria del frontend.

    Returns:
        dict con respuesta (str).

    Raises:
        AppError: CLAUDE_UNAVAILABLE | AGENT_LOOP_ERROR.
    """
    messages = [
        *[{"role": m["role"], "content": m["content"]} for m in historial],
        {"role": "user", "content": mensaje},
    ]
    client = get_anthropic()
    try:
        res = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT_CONFIGURADOR,
            messages=messages,
        )
        texto = "".join(b.text for b in res.content if b.type == "text")
        return {"respuesta": texto}
    except Exception as err:
        status = getattr(err, "status_code", 0)
        if status in (429, 503, 529):
            raise AppError("Claude no está disponible temporalmente", "CLAUDE_UNAVAILABLE", 503)
        logger.error("Error en agente configurador: %s", str(err))
        raise AppError("Error en el agente configurador", "AGENT_LOOP_ERROR", 500)
