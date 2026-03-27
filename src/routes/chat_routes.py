"""
Routing + validación de entrada para /api/chat y /api/conversaciones.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.controllers import chat_controller
from src.middleware.auth import get_current_user
from src.middleware.rate_limiter import rate_limit_by_key

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])
conversaciones_router = APIRouter(prefix="/api/conversaciones", tags=["conversaciones"])


class ChatRequest(BaseModel):
    """Body de POST /api/chat."""
    mensaje: str = Field(min_length=1, max_length=4000)
    conversacionId: str | None = None


@chat_router.post("")
async def chat(request: Request, body: ChatRequest, user: dict = Depends(get_current_user)):
    """
    POST /api/chat
    Body: { mensaje, conversacionId? }
    Rate limit: 20 req/min por userId (Redis o memoria).
    """
    allowed = await rate_limit_by_key(f"chat:{user['userId']}", max_requests=20, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"error": True, "message": "Demasiados mensajes, esperá un momento", "code": "RATE_LIMIT_EXCEEDED"},
        )
    return await chat_controller.chat(body.mensaje, body.conversacionId, user["userId"])


@conversaciones_router.get("")
async def listar(user: dict = Depends(get_current_user)):
    """GET /api/conversaciones — lista las últimas 20 conversaciones."""
    return await chat_controller.listar_conversaciones(user["userId"])


@conversaciones_router.get("/{conv_id}")
async def cargar(conv_id: str, user: dict = Depends(get_current_user)):
    """GET /api/conversaciones/{conv_id} — carga una conversación formateada."""
    return await chat_controller.cargar_conversacion(conv_id, user["userId"])
