"""
Lógica de negocio de conversaciones.
Obtener/crear conversación, título automático y formateo para el frontend.
"""

from src.integrations.anthropic_client import get_anthropic
from src.repositories import conversacion_repository as conv_repo
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("chatService")


def _extraer_texto_bloque(content) -> str:
    """Extrae texto visible de un bloque de contenido (string o array)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


async def obtener_o_crear_conversacion(conv_id: str | None, user_id: str) -> dict:
    """
    Obtiene una conversación existente o crea una nueva.

    Args:
        conv_id: UUID existente o None para crear.
        user_id: UUID del usuario.

    Returns:
        dict con la conversación.

    Raises:
        AppError: CONVERSACION_NOT_FOUND si el ID no existe o no pertenece al usuario.
    """
    if conv_id:
        conv = await conv_repo.find_by_id(conv_id, user_id)
        if not conv:
            raise AppError("Conversación no encontrada", "CONVERSACION_NOT_FOUND", 404)
        return conv
    return await conv_repo.create(user_id)


async def actualizar_mensajes(conv_id: str, messages: list, user_id: str) -> dict:
    """
    Actualiza los mensajes de una conversación.

    Args:
        conv_id: UUID de la conversación.
        messages: Array completo de mensajes actualizado.
        user_id: UUID del usuario (ownership check).

    Returns:
        dict con la conversación actualizada.
    """
    return await conv_repo.update_messages(conv_id, messages, user_id)


async def listar_conversaciones(user_id: str) -> dict:
    """
    Lista las últimas 20 conversaciones del usuario.

    Args:
        user_id: UUID del usuario.

    Returns:
        dict con conversaciones (list).
    """
    conversaciones = await conv_repo.find_by_user(user_id)
    return {"conversaciones": conversaciones}


async def generar_titulo_background(conv_id: str, user_id: str, primer_mensaje: str) -> None:
    """
    Genera un título corto con Claude y lo persiste. Fire-and-forget.

    Args:
        conv_id: UUID de la conversación.
        user_id: UUID del usuario (ownership check).
        primer_mensaje: Primer mensaje del usuario para generar contexto.
    """
    try:
        client = get_anthropic()
        res = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": (
                    f"Generá un título de máximo 4 palabras en español para una conversación "
                    f"que empieza con: '{primer_mensaje}'. Respondé SOLO el título, sin comillas "
                    f"ni puntuación."
                ),
            }],
        )
        titulo = res.content[0].text.strip()
        await conv_repo.update(conv_id, user_id, {"titulo": titulo})
        logger.info("Título generado convId=%s titulo=%s", conv_id, titulo)
    except Exception as err:
        logger.error("Error generando título convId=%s: %s", conv_id, str(err))


async def cargar_conversacion_formateada(conv_id: str, user_id: str) -> dict:
    """
    Carga una conversación y formatea sus mensajes para el frontend.
    Filtra tool_use/tool_result — solo devuelve mensajes con texto visible.

    Args:
        conv_id: UUID de la conversación.
        user_id: UUID del usuario.

    Returns:
        dict con conversacion ({id, titulo}) y mensajes (list).

    Raises:
        AppError: CONVERSACION_NOT_FOUND si no existe.
    """
    conversacion = await conv_repo.find_by_id(conv_id, user_id)
    if not conversacion:
        raise AppError("Conversación no encontrada", "CONVERSACION_NOT_FOUND", 404)

    mensajes = []
    for m in conversacion.get("messages") or []:
        if m.get("role") not in ("user", "assistant"):
            continue
        content = m.get("content", "")
        if isinstance(content, list):
            if not any(b.get("type") == "text" for b in content):
                continue
        elif not (isinstance(content, str) and len(content) > 0):
            continue

        mensajes.append({
            "id": m.get("id"),
            "rol": "user" if m["role"] == "user" else "agent",
            "texto": _extraer_texto_bloque(content),
            "timestamp": m.get("timestamp", conversacion.get("updated_at")),
        })

    return {
        "conversacion": {"id": conversacion["id"], "titulo": conversacion.get("titulo")},
        "mensajes": mensajes,
    }
