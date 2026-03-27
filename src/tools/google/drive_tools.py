"""
Herramienta Drive: búsqueda de archivos por nombre o contenido.
Sanitiza query contra FTS injection.
"""

import re
from datetime import datetime

from googleapiclient.discovery import build

from src.integrations.google_client import get_google_client
from src.utils.logger import get_logger

logger = get_logger("drive")

MIME_LABELS = {
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheets",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.google-apps.folder": "Carpeta",
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
}


async def buscar_drive(user_id: str, query: str, **_) -> list:
    """
    Busca archivos en Google Drive por nombre o contenido.
    Sanitiza la query contra inyección FTS.

    Returns:
        Lista de dicts con nombre, tipo, url, modificado.
    """
    creds = await get_google_client(user_id, "drive")
    drive = build("drive", "v3", credentials=creds)

    # Sanitizar: remover comillas, paréntesis, backslashes, dos puntos (FTS operators)
    termino = re.sub(r"['\"\\\(\):]", " ", query).strip()[:200]
    q = f"(name contains '{termino}' or fullText contains '{termino}') and trashed = false"

    res = drive.files().list(
        q=q, pageSize=10,
        fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        orderBy="modifiedTime desc",
    ).execute()

    archivos = res.get("files", [])
    logger.info("Búsqueda Drive userId=%s query=%s resultados=%d", user_id, query, len(archivos))

    resultado = []
    for f in archivos:
        mod = f.get("modifiedTime", "")
        if mod:
            try:
                mod = datetime.fromisoformat(mod.replace("Z", "+00:00")).strftime("%d/%m/%Y")
            except Exception:
                pass
        resultado.append({
            "nombre": f.get("name"),
            "tipo": MIME_LABELS.get(f.get("mimeType", ""), f.get("mimeType", "")),
            "url": f.get("webViewLink", ""),
            "modificado": mod,
        })
    return resultado
