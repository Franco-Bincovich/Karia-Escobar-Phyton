"""
Routing + validación de entrada para /api/auth.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.controllers.auth_controller import login_controller
from src.middleware.auth import get_current_user
from src.middleware.rate_limiter import rate_limit_by_key
from src.middleware.audit import auditar_accion
from src.services.auth_service import cambiar_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# slowapi limiter se mantiene para otros módulos que lo importan (integraciones, documentos)
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    """Body de POST /api/auth/login."""
    email: EmailStr
    password: str = Field(min_length=6)


class CambiarPasswordRequest(BaseModel):
    """Body de POST /api/auth/cambiar-password."""
    password_actual: str = Field(min_length=1)
    password_nuevo: str = Field(min_length=8)


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """
    POST /api/auth/login
    Body: { email, password }
    Responde con { token, user } si las credenciales son válidas.
    Rate limit: 3 requests por email cada 15 minutos (Redis o memoria).
    """
    allowed = await rate_limit_by_key(f"login:{body.email}", max_requests=3, window_seconds=900)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"error": True, "message": "Demasiados intentos, intentá más tarde", "code": "RATE_LIMIT_EXCEEDED"},
        )
    return await login_controller(body.email, body.password)


@router.post("/cambiar-password")
async def cambiar_password_endpoint(
    request: Request, body: CambiarPasswordRequest, user: dict = Depends(get_current_user),
):
    """
    POST /api/auth/cambiar-password
    Body: { password_actual, password_nuevo }
    Requiere JWT. Valida la contraseña actual y actualiza con la nueva.
    """
    resultado = await cambiar_password(user["userId"], body.password_actual, body.password_nuevo)
    await auditar_accion(user["userId"], "cambio_password", request.client.host)
    return resultado
