"""
Loop agéntico de Claude: gestiona iteraciones, tool_use y end_turn.
Máximo 10 iteraciones con ejecución paralela de tools.
"""

import asyncio
import json

from src.config.index import settings
from src.integrations.anthropic_client import get_anthropic
from src.tools import ejecutar_tool
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("agentLoop")

MAX_ITERACIONES = 10
MODEL = "claude-sonnet-4-5-20250514"
MAX_TOKENS = 4096

_semaphore = asyncio.Semaphore(settings.ANTHROPIC_MAX_CONCURRENT)


def _extraer_texto(contenido: list) -> str:
    """Extrae bloques de texto del content de Claude."""
    return "".join(b.text for b in contenido if b.type == "text")


async def _ejecutar_tool_seguro(bloque, user_id: str) -> dict:
    """Ejecuta una tool capturando errores para devolver tool_result."""
    try:
        resultado = await ejecutar_tool(bloque.name, bloque.input, user_id)
        return {
            "type": "tool_result",
            "tool_use_id": bloque.id,
            "content": json.dumps(resultado, ensure_ascii=False),
        }
    except Exception as e:
        logger.warning("Error ejecutando tool %s: %s", bloque.name, str(e))
        return {
            "type": "tool_result",
            "tool_use_id": bloque.id,
            "content": f"Error: {str(e)}",
            "is_error": True,
        }


def _content_to_dicts(content) -> list[dict]:
    """Convierte bloques del SDK de Anthropic a dicts serializables."""
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return result


async def ejecutar_loop(
    messages: list,
    system_prompt: str,
    tools: list,
    user_id: str,
) -> dict:
    """
    Ejecuta el loop agéntico con soporte de herramientas.

    Args:
        messages: Historial de mensajes.
        system_prompt: System prompt completo.
        tools: Lista de tool definitions para Anthropic.
        user_id: ID del usuario autenticado.

    Returns:
        dict con respuesta (str) y mensajes_actualizados (list).

    Raises:
        AppError: CLAUDE_UNAVAILABLE si Claude no responde.
        AppError: AGENT_LOOP_ERROR si se superan las iteraciones.
    """
    client = get_anthropic()
    iteraciones = 0

    try:
        while iteraciones < MAX_ITERACIONES:
            iteraciones += 1

            kwargs = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": system_prompt,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            if _semaphore.locked():
                logger.debug("Semaphore lleno, request en cola userId=%s", user_id)
            async with _semaphore:
                respuesta = client.messages.create(**kwargs)

            logger.info(
                "Respuesta de Claude iter=%d stop=%s userId=%s",
                iteraciones, respuesta.stop_reason, user_id,
            )

            content_dicts = _content_to_dicts(respuesta.content)

            if respuesta.stop_reason == "end_turn":
                messages.append({"role": "assistant", "content": content_dicts})
                return {
                    "respuesta": _extraer_texto(respuesta.content),
                    "mensajes_actualizados": messages,
                }

            if respuesta.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": content_dicts})
                tool_blocks = [b for b in respuesta.content if b.type == "tool_use"]
                resultados = await asyncio.gather(
                    *[_ejecutar_tool_seguro(b, user_id) for b in tool_blocks]
                )
                messages.append({"role": "user", "content": list(resultados)})
                continue

            break  # stop_reason inesperado

        raise AppError("El agente alcanzó el máximo de iteraciones", "AGENT_LOOP_ERROR", 500)

    except AppError:
        raise
    except Exception as err:
        status = getattr(err, "status_code", 0)
        if status in (429, 503, 529):
            raise AppError("Claude no está disponible temporalmente", "CLAUDE_UNAVAILABLE", 503)
        logger.error("Error en loop del agente: %s userId=%s", str(err), user_id)
        raise AppError("Error en el loop del agente", "AGENT_LOOP_ERROR", 500)
