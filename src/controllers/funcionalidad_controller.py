"""
Controller de funcionalidades.
Solo orquestación — sin lógica de negocio.
"""

from src.services import funcionalidad_service


async def listar_controller(user: dict) -> dict:
    """
    Lista funcionalidades del usuario.

    Args:
        user: Usuario autenticado.

    Returns:
        dict con funcionalidades (list).
    """
    funcionalidades = await funcionalidad_service.listar(user["userId"])
    return {"funcionalidades": funcionalidades}


async def crear_controller(datos: dict, user: dict) -> dict:
    """
    Crea una funcionalidad.

    Args:
        datos: dict con nombre, descripcion, system_prompt.
        user: Usuario autenticado.

    Returns:
        dict con la funcionalidad creada.
    """
    return await funcionalidad_service.crear(user["userId"], datos)


async def toggle_controller(func_id: str, user: dict) -> dict:
    """
    Alterna activo/inactivo.

    Args:
        func_id: UUID de la funcionalidad.
        user: Usuario autenticado.

    Returns:
        dict con ok y activo.
    """
    row = await funcionalidad_service.toggle_activo(func_id, user["userId"])
    return {"ok": True, "activo": row["activo"]}


async def eliminar_controller(func_id: str, user: dict) -> dict:
    """
    Elimina una funcionalidad.

    Args:
        func_id: UUID de la funcionalidad.
        user: Usuario autenticado.

    Returns:
        dict con ok.
    """
    await funcionalidad_service.eliminar(func_id, user["userId"])
    return {"ok": True}
