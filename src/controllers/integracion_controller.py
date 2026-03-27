"""
Controller de integraciones no-OAuth: listar, conectar API key, toggle, desconectar.
El flujo OAuth2 de Google vive en oauth_controller.py.
"""

from src.services import integracion_service


async def listar_controller(user: dict) -> dict:
    """GET /api/integraciones — lista sin credenciales."""
    integraciones = await integracion_service.listar_integraciones(user["userId"])
    return {"integraciones": integraciones}


async def conectar_api_key_controller(datos: dict, user: dict) -> dict:
    """POST /api/integraciones/apikey — guarda API key cifrada."""
    await integracion_service.guardar_api_key(user["userId"], datos["tipo"], datos["apiKey"])
    return {"ok": True, "tipo": datos["tipo"]}


async def toggle_controller(tipo: str, user: dict) -> dict:
    """PATCH /api/integraciones/{tipo}/toggle."""
    result = await integracion_service.toggle_activo(user["userId"], tipo)
    return {"ok": True, "activo": result["activo"]}


async def desconectar_controller(tipo: str, user: dict) -> dict:
    """DELETE /api/integraciones/{tipo}."""
    await integracion_service.desconectar(user["userId"], tipo)
    return {"ok": True}
