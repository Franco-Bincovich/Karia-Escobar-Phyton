"""
Routing + validación de entrada para /api/chat y /api/conversaciones.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter

from src.controllers import chat_controller
from src.middleware.auth import get_current_user

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])
conversaciones_router = APIRouter(prefix="/api/conversaciones", tags=["conversaciones"])


def _get_user_id_or_ip(request: Request) -> str:
    """Extrae userId del JWT si está disponible, sino usa IP."""
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user.get("userId", request.client.host)
    return request.client.host


chat_limiter = Limiter(key_func=_get_user_id_or_ip)


class ChatRequest(BaseModel):
    """Body de POST /api/chat."""
    mensaje: str = Field(min_length=1, max_length=4000)
    conversacionId: str | None = None


@chat_router.post("")
@chat_limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest, user: dict = Depends(get_current_user)):
    """
    POST /api/chat
    Body: { mensaje, conversacionId? }
    Rate limit: 20 req/min por userId.
    """
    request.state.user = user
    return await chat_controller.chat(body.mensaje, body.conversacionId, user["userId"])


@conversaciones_router.get("")
async def listar(user: dict = Depends(get_current_user)):
    """GET /api/conversaciones — lista las últimas 20 conversaciones."""
    return await chat_controller.listar_conversaciones(user["userId"])


@conversaciones_router.get("/{conv_id}")
async def cargar(conv_id: str, user: dict = Depends(get_current_user)):
    """GET /api/conversaciones/{conv_id} — carga una conversación formateada."""
    return await chat_controller.cargar_conversacion(conv_id, user["userId"])
