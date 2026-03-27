"""
Controller de chat y conversaciones.
Solo orquestación — sin lógica de negocio.
"""

import asyncio

from src.agent import ejecutar_agente
from src.services import chat_service
from src.utils.logger import get_logger

logger = get_logger("chatController")


async def chat(mensaje: str, conversacion_id: str | None, user_id: str) -> dict:
    """
    Orquesta el flujo de POST /api/chat.

    Args:
        mensaje: Texto del usuario.
        conversacion_id: UUID existente o None para nueva conversación.
        user_id: UUID del usuario autenticado.

    Returns:
        dict con respuesta (str) y conversacionId (str).
    """
    conversacion = await chat_service.obtener_o_crear_conversacion(conversacion_id, user_id)
    historial = conversacion.get("messages") or []

    logger.info(
        "Iniciando chat userId=%s convId=%s msgLen=%d",
        user_id, conversacion["id"], len(mensaje),
    )

    resultado = await ejecutar_agente(mensaje, historial, user_id)
    await chat_service.actualizar_mensajes(conversacion["id"], resultado["mensajes_actualizados"], user_id)

    # Generar título en background para conversaciones nuevas
    if not conversacion_id:
        asyncio.create_task(chat_service.generar_titulo_background(conversacion["id"], user_id, mensaje))

    return {"respuesta": resultado["respuesta"], "conversacionId": conversacion["id"]}


async def listar_conversaciones(user_id: str) -> dict:
    """
    Lista las últimas 20 conversaciones del usuario.

    Args:
        user_id: UUID del usuario autenticado.

    Returns:
        dict con conversaciones (list).
    """
    logger.info("Listando conversaciones userId=%s", user_id)
    return await chat_service.listar_conversaciones(user_id)


async def cargar_conversacion(conv_id: str, user_id: str) -> dict:
    """
    Carga una conversación formateada para el frontend.

    Args:
        conv_id: UUID de la conversación.
        user_id: UUID del usuario autenticado.

    Returns:
        dict con conversacion y mensajes.
    """
    logger.info("Cargando conversación userId=%s convId=%s", user_id, conv_id)
    return await chat_service.cargar_conversacion_formateada(conv_id, user_id)
