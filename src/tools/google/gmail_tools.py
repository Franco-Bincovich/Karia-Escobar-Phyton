"""
Herramientas Gmail: leer bandeja no leída y enviar emails.
"""

import base64
from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from src.integrations.google_client import get_google_client
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("gmail")

TZ = ZoneInfo("America/Argentina/Buenos_Aires")


async def leer_gmail(user_id: str, cantidad: int = 5, **_) -> list:
    """
    Lee los últimos N emails no leídos del usuario.

    Returns:
        Lista de dicts con id, de, asunto, fecha, resumen.
    """
    creds = await get_google_client(user_id, "gmail")
    gmail = build("gmail", "v1", credentials=creds)

    lista = gmail.users().messages().list(
        userId="me", maxResults=min(cantidad, 20), q="is:unread",
    ).execute()

    mensajes = lista.get("messages", [])
    if not mensajes:
        return []

    resultado = []
    for m in mensajes:
        detalle = gmail.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in (detalle.get("payload", {}).get("headers", []))}
        fecha_raw = headers.get("Date", "")
        try:
            fecha = datetime.strptime(fecha_raw[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha_str = fecha_raw
        resultado.append({
            "id": detalle["id"], "de": headers.get("From", ""),
            "asunto": headers.get("Subject", ""), "fecha": fecha_str,
            "resumen": detalle.get("snippet", ""),
        })
    return resultado


async def enviar_gmail(user_id: str, para: str, asunto: str, cuerpo: str, **_) -> dict:
    """
    Envía un email desde la cuenta del usuario. Valida CRLF en para y asunto.

    Returns:
        dict con ok, para, asunto.
    """
    if "\r" in para or "\n" in para:
        raise AppError("Dirección de email inválida", "EMAIL_INVALIDO", 400)
    asunto_limpio = asunto.replace("\r", " ").replace("\n", " ").strip()

    creds = await get_google_client(user_id, "gmail")
    gmail = build("gmail", "v1", credentials=creds)

    mime = f"To: {para}\r\nSubject: {asunto_limpio}\r\nContent-Type: text/plain; charset=utf-8\r\nMIME-Version: 1.0\r\n\r\n{cuerpo}"
    raw = base64.urlsafe_b64encode(mime.encode()).decode()

    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    logger.info("Email enviado userId=%s para=%s", user_id, para)
    return {"ok": True, "para": para, "asunto": asunto_limpio}
