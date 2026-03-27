"""
Búsqueda web genérica: DuckDuckGo scraper con httpx + BeautifulSoup.
Incluye protección SSRF: solo hosts permitidos y sin IPs privadas.
"""

import ipaddress
import socket
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("search/web")

TIMEOUT = 8.0
UA = "KarIA-Escobar/1.0 (+https://karia.ar)"
DDG_URL = "https://html.duckduckgo.com/html/"

ALLOWED_HOSTS = {"duckduckgo.com", "html.duckduckgo.com", "infoleg.gob.ar",
                 "www.infoleg.gob.ar", "saij.gob.ar", "www.saij.gob.ar",
                 "escobar.gob.ar", "www.escobar.gob.ar"}


def _validar_url(url: str) -> bool:
    """Valida que la URL sea HTTPS, host permitido y no IP privada."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = parsed.hostname or ""
    if host not in ALLOWED_HOSTS:
        return False
    try:
        ip = socket.gethostbyname(host)
        if ipaddress.ip_address(ip).is_private:
            return False
    except socket.gaierror:
        return False
    return True


async def fetch_html(url: str) -> str | None:
    """Descarga HTML con timeout, User-Agent institucional y protección SSRF."""
    if not _validar_url(url):
        logger.warning("URL bloqueada por SSRF: %s", url)
        return None
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            res = await client.get(url, headers={"User-Agent": UA}, follow_redirects=True)
            res.raise_for_status()
            return res.text
    except httpx.HTTPStatusError as e:
        raise AppError(f"HTTP {e.response.status_code} al obtener {url}", "FETCH_ERROR", 502)
    except Exception as e:
        raise AppError(f"Error al obtener {url}: {e}", "FETCH_ERROR", 502)


async def buscar_web(query: str, user_id: str, maxResultados: int = 5, **_) -> dict:
    """
    Busca en DuckDuckGo y devuelve resultados.

    Returns:
        dict con query y resultados [{titulo, url, fragmento}].
    """
    logger.info("Búsqueda web userId=%s query=%s", user_id, query)
    url = f"{DDG_URL}?q={quote_plus(query)}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    resultados = []

    for el in soup.select(".result__body")[:min(maxResultados, 10)]:
        titulo = el.select_one(".result__title")
        fragmento = el.select_one(".result__snippet")
        enlace = el.select_one("a.result__url")
        if titulo:
            resultados.append({
                "titulo": titulo.get_text(strip=True),
                "url": enlace.get("href", "") if enlace else "",
                "fragmento": fragmento.get_text(strip=True) if fragmento else "",
            })

    logger.info("Búsqueda web completada userId=%s cantidad=%d", user_id, len(resultados))
    return {"query": query, "resultados": resultados}
