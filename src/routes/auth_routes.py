"""
Routing + validación de entrada para /api/auth.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.controllers.auth_controller import login_controller
from src.middleware.rate_limiter import rate_limit_by_key

router = APIRouter(prefix="/api/auth", tags=["auth"])

# slowapi limiter se mantiene para otros módulos que lo importan (integraciones, documentos)
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    """Body de POST /api/auth/login."""
    email: EmailStr
    password: str = Field(min_length=6)


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """
    POST /api/auth/login
    Body: { email, password }
    Responde con { token, user } si las credenciales son válidas.
    Rate limit: 10 requests por email cada 15 minutos (Redis o memoria).
    """
    allowed = await rate_limit_by_key(f"login:{body.email}", max_requests=10, window_seconds=900)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"error": True, "message": "Demasiados intentos, intentá más tarde", "code": "RATE_LIMIT_EXCEEDED"},
        )
    return await login_controller(body.email, body.password)
