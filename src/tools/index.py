"""
Registro central de herramientas del agente KarIA Escobar.
TOOLS se pasa a la API de Anthropic. ejecutar_tool despacha la ejecución.
"""

import asyncio

from src.tools.tool_definitions import TOOLS
from src.tools.excel_tools import generar_excel, analizar_excel_avanzado
from src.tools.word_tools import generar_word
from src.tools.search.web import buscar_web
from src.tools.search.normativa import buscar_normativa
from src.tools.search.ordenanzas import buscar_ordenanzas
from src.tools.google.gmail_tools import leer_gmail, enviar_gmail
from src.tools.google.calendar_tools import leer_calendar, crear_evento
from src.tools.google.drive_tools import buscar_drive
from src.tools.gamma_tools import generar_presentacion
from src.tools.vision_tools import analizar_imagen
from src.utils.app_error import AppError

# Tools que generan archivos — userId prefija el nombre (anti-IDOR)
FILE_TOOLS = {"generar_excel", "generar_word", "analizar_imagen"}

# Tools que necesitan userId para credenciales Google/API
USER_TOOLS = {
    "leer_gmail", "enviar_gmail", "leer_calendar", "crear_evento",
    "buscar_drive", "buscar_web", "generar_presentacion",
    "analizar_documento", "analizar_excel_basico", "analizar_excel_avanzado",
}

# Mapa de despacho: nombre → función async
_MAPA_TOOLS = {
    "generar_excel": generar_excel,
    "generar_word": generar_word,
    "analizar_documento": lambda **kw: kw,  # wrapper — Claude procesa el resultado
    "analizar_excel_basico": lambda **kw: kw,
    "analizar_excel_avanzado": analizar_excel_avanzado,
    "leer_gmail": leer_gmail,
    "enviar_gmail": enviar_gmail,
    "leer_calendar": leer_calendar,
    "crear_evento": crear_evento,
    "buscar_drive": buscar_drive,
    "buscar_web": buscar_web,
    "buscar_normativa": buscar_normativa,
    "buscar_ordenanzas": buscar_ordenanzas,
    "generar_presentacion": generar_presentacion,
    "analizar_imagen": analizar_imagen,
}


async def ejecutar_tool(nombre: str, params: dict, user_id: str):
    """
    Ejecuta una herramienta por nombre con los parámetros dados.

    Args:
        nombre: Nombre de la tool (debe coincidir con TOOLS[].name).
        params: Parámetros de la tool.
        user_id: ID del usuario autenticado.

    Returns:
        Resultado de la tool.

    Raises:
        AppError: TOOL_NOT_FOUND si la tool no existe.
    """
    fn = _MAPA_TOOLS.get(nombre)
    if not fn:
        raise AppError(f"Tool desconocida: {nombre}", "TOOL_NOT_FOUND", 400)

    if nombre in FILE_TOOLS or nombre in USER_TOOLS:
        params["user_id"] = user_id

    result = fn(**params)
    if asyncio.iscoroutine(result):
        return await result
    return result
