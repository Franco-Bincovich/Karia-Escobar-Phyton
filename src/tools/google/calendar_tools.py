"""
Herramientas Calendar: listar eventos próximos y crear evento.
Timezone: America/Argentina/Buenos_Aires.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from src.integrations.google_client import get_google_client
from src.utils.logger import get_logger

logger = get_logger("calendar")

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
TZ_NAME = "America/Argentina/Buenos_Aires"


async def leer_calendar(user_id: str, dias: int = 7, **_) -> list:
    """
    Lista los eventos de los próximos N días (máx 60).

    Returns:
        Lista de dicts con id, titulo, fecha, hora, lugar, descripcion.
    """
    creds = await get_google_client(user_id, "calendar")
    cal = build("calendar", "v3", credentials=creds)

    ahora = datetime.now(TZ)
    hasta = ahora + timedelta(days=min(dias, 60))

    res = cal.events().list(
        calendarId="primary", timeMin=ahora.isoformat(), timeMax=hasta.isoformat(),
        maxResults=25, singleEvents=True, orderBy="startTime", timeZone=TZ_NAME,
    ).execute()

    resultado = []
    for ev in res.get("items", []):
        inicio = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        if ev.get("start", {}).get("dateTime"):
            dt = datetime.fromisoformat(inicio)
            hora = dt.strftime("%H:%M")
        else:
            hora = "Todo el día"
        fecha = inicio.split("T")[0] if "T" in inicio else inicio
        resultado.append({
            "id": ev.get("id"), "titulo": ev.get("summary", "(sin título)"),
            "fecha": fecha, "hora": hora,
            "lugar": ev.get("location", ""), "descripcion": ev.get("description", ""),
        })
    return resultado


async def crear_evento(
    user_id: str, titulo: str, fecha: str, hora: str,
    duracionMinutos: int = 60, descripcion: str = "", **_,
) -> dict:
    """
    Crea un evento en el calendario principal.

    Args:
        fecha: YYYY-MM-DD
        hora: HH:MM (24hs)

    Returns:
        dict con ok, id, titulo, inicio, url.
    """
    creds = await get_google_client(user_id, "calendar")
    cal = build("calendar", "v3", credentials=creds)

    inicio = datetime.fromisoformat(f"{fecha}T{hora}:00").replace(tzinfo=TZ)
    fin = inicio + timedelta(minutes=duracionMinutos)

    res = cal.events().insert(
        calendarId="primary",
        body={
            "summary": titulo, "description": descripcion or "",
            "start": {"dateTime": inicio.isoformat(), "timeZone": TZ_NAME},
            "end": {"dateTime": fin.isoformat(), "timeZone": TZ_NAME},
        },
    ).execute()

    logger.info("Evento creado userId=%s titulo=%s fecha=%s", user_id, titulo, fecha)
    return {
        "ok": True, "id": res.get("id"), "titulo": res.get("summary"),
        "inicio": res.get("start", {}).get("dateTime"), "url": res.get("htmlLink", ""),
    }
