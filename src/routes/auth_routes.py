"""
Routing + validación de entrada para /api/auth.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.controllers.auth_controller import login_controller

router = APIRouter(prefix="/api/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    """Body de POST /api/auth/login."""
    email: EmailStr
    password: str = Field(min_length=6)


@router.post("/login")
@limiter.limit("10/15minutes")
async def login(request: Request, body: LoginRequest):
    """
    POST /api/auth/login
    Body: { email, password }
    Responde con { token, user } si las credenciales son válidas.
    Rate limit: 10 requests por IP cada 15 minutos.
    """
    resultado = await login_controller(body.email, body.password)
    return resultado
