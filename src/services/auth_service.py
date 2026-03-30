"""
Lógica de negocio de autenticación.
El controller solo orquesta — toda la lógica vive acá.
"""

import time

import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError

from src.config.index import settings
from src.repositories import user_repository as user_repo
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("authService")

# Hash ficticio para bcrypt.checkpw() cuando el usuario no existe — previene timing attack (H2)
DUMMY_HASH = b"$2b$12$KIXHkMhXiQj5Y8rPvbLOXuGpQSHbL8JJQf3bXvRmNpT8kJhGqD4Hy"

# Rate limit por cuenta — {email: {count, expires_at}} (H3)
MAX_INTENTOS = 10
TTL_SECONDS = 15 * 60  # 15 minutos
_intentos_fallidos: dict[str, dict] = {}

JWT_ALGORITHM = "HS256"
JWT_EXPIRES_SECONDS = 8 * 60 * 60  # 8 horas


def _registrar_fallo(email: str) -> None:
    entrada = _intentos_fallidos.get(email, {"count": 0})
    entrada["count"] += 1
    entrada["expires_at"] = time.time() + TTL_SECONDS
    _intentos_fallidos[email] = entrada


def _resetear_intentos(email: str) -> None:
    _intentos_fallidos.pop(email, None)


def _esta_bloqueado(email: str) -> bool:
    entrada = _intentos_fallidos.get(email)
    if not entrada:
        return False
    if time.time() > entrada.get("expires_at", 0):
        _intentos_fallidos.pop(email, None)
        return False
    return entrada["count"] >= MAX_INTENTOS


async def login(email: str, password: str) -> dict:
    """Autentica con email/password. Retorna {token, user} o lanza AppError."""
    # 1. Verificar bloqueo por intentos fallidos (H3)
    if _esta_bloqueado(email):
        raise AppError(
            "Cuenta bloqueada temporalmente por múltiples intentos fallidos",
            "ACCOUNT_LOCKED",
            429,
        )

    # 2. Buscar usuario y comparar siempre con bcrypt — previene timing attack (H2)
    usuario = await user_repo.find_by_email(email)
    hash_a_comparar = usuario["password_hash"].encode() if usuario else DUMMY_HASH
    coincide = bcrypt.checkpw(password.encode(), hash_a_comparar)

    if not usuario or not coincide:
        _registrar_fallo(email)
        raise AppError("Credenciales inválidas", "INVALID_CREDENTIALS", 401)

    # 3. Verificar que el usuario esté activo
    if not usuario.get("activo", True):
        raise AppError("Usuario inactivo", "USER_INACTIVE", 403)

    _resetear_intentos(email)

    # 4. Generar JWT
    payload = {
        "userId": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "exp": int(time.time()) + JWT_EXPIRES_SECONDS,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)

    logger.info("Login exitoso userId=%s email=%s", usuario["id"], usuario["email"])

    # 5. Retornar token y datos públicos
    return {
        "token": token,
        "user": {
            "id": usuario["id"],
            "email": usuario["email"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
            "needs_password_reset": usuario.get("needs_password_reset", False),
        },
    }


async def cambiar_password(user_id: str, password_actual: str, password_nuevo: str) -> dict:
    """Cambia la contraseña verificando la actual. Min 8 chars + 1 número."""
    if len(password_nuevo) < 8 or not any(c.isdigit() for c in password_nuevo):
        raise AppError(
            "La nueva contraseña debe tener al menos 8 caracteres y 1 número",
            "PASSWORD_INVALIDO",
            400,
        )

    usuario = await user_repo.find_by_id(user_id)
    if not usuario:
        raise AppError("Usuario no encontrado", "USER_NOT_FOUND", 404)

    if not bcrypt.checkpw(password_actual.encode(), usuario["password_hash"].encode()):
        raise AppError("La contraseña actual es incorrecta", "PASSWORD_INCORRECTO", 401)

    nuevo_hash = bcrypt.hashpw(password_nuevo.encode(), bcrypt.gensalt(rounds=12)).decode()
    await user_repo.update(user_id, {"password_hash": nuevo_hash, "needs_password_reset": False})

    logger.info("Password cambiado userId=%s", user_id)
    return {"message": "Contraseña actualizada correctamente"}


async def verificar_token(token: str) -> dict:
    """Verifica y decodifica un JWT. Retorna {userId, email, rol}."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"userId": payload["userId"], "email": payload["email"], "rol": payload["rol"]}
    except ExpiredSignatureError:
        raise AppError("Token expirado", "TOKEN_EXPIRED", 401)
    except JWTError:
        raise AppError("Token inválido", "TOKEN_INVALID", 401)
