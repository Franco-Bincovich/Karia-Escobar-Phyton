"""
Constantes de dominio para integraciones.
Un solo lugar para agregar o quitar tipos y servicios.
"""

TIPOS_VALIDOS = ["anthropic", "openai", "gmail", "drive", "calendar", "perplexity", "gamma"]

TIPOS_API_KEY = ["anthropic", "openai", "perplexity", "gamma"]

TIPOS_GOOGLE = ["gmail", "drive", "calendar"]

SCOPES_POR_SERVICIO = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ],
    "drive": ["https://www.googleapis.com/auth/drive.readonly"],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
}

SERVICIOS_VALIDOS = list(SCOPES_POR_SERVICIO.keys())
