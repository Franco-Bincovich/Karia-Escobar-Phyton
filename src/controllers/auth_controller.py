"""
Controller de autenticación.
Solo orquestación — sin lógica de negocio.
Toda la lógica vive en auth_service.py.
"""

from src.services import auth_service


async def login_controller(email: str, password: str) -> dict:
    """
    Orquesta el login llamando al service.

    Args:
        email: Email del usuario.
        password: Contraseña en texto plano.

    Returns:
        dict con token y user.
    """
    return await auth_service.login(email, password)
