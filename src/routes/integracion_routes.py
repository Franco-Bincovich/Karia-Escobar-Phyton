"""
Routing + validación de entrada para /api/integraciones.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.controllers import integracion_controller as ctrl
from src.controllers import oauth_controller as oauth_ctrl
from src.middleware.auth import get_current_user
from src.routes.auth_routes import limiter

router = APIRouter(prefix="/api/integraciones", tags=["integraciones"])


class ApiKeyRequest(BaseModel):
    """Body de POST /api/integraciones/apikey."""
    tipo: str = Field(pattern=r"^(anthropic|openai|perplexity|gamma)$")
    apiKey: str = Field(min_length=1)


class GoogleAuthRequest(BaseModel):
    """Body de POST /api/integraciones/google/auth."""
    servicios: str = Field(min_length=1)
    clientId: str | None = None
    clientSecret: str | None = None


@router.get("")
async def listar(user: dict = Depends(get_current_user)):
    """GET /api/integraciones — lista sin credenciales."""
    return await ctrl.listar_controller(user)


@router.post("/apikey")
@limiter.limit("100/15minutes")
async def conectar_apikey(request: Request, body: ApiKeyRequest, user: dict = Depends(get_current_user)):
    """POST /api/integraciones/apikey — guarda API key cifrada."""
    return await ctrl.conectar_api_key_controller(body.model_dump(), user)


@router.post("/google/auth")
@limiter.limit("100/15minutes")
async def google_auth(request: Request, body: GoogleAuthRequest, user: dict = Depends(get_current_user)):
    """POST /api/integraciones/google/auth — inicia OAuth Google."""
    return await oauth_ctrl.conectar_google_controller(body.model_dump(), user)


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", error: str | None = None):
    """GET /api/integraciones/google/callback — callback OAuth (sin JWT)."""
    return await oauth_ctrl.callback_google_controller(code, state, error)


@router.patch("/{tipo}/toggle")
async def toggle(tipo: str, user: dict = Depends(get_current_user)):
    """PATCH /api/integraciones/{tipo}/toggle."""
    return await ctrl.toggle_controller(tipo, user)


@router.delete("/{tipo}")
async def desconectar(tipo: str, user: dict = Depends(get_current_user)):
    """DELETE /api/integraciones/{tipo}."""
    return await ctrl.desconectar_controller(tipo, user)
