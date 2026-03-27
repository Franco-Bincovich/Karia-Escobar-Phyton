"""
Scraping de Infoleg y SAIJ — bases legales oficiales de Argentina.
"""

import asyncio
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from src.tools.search.web import fetch_html
from src.utils.logger import get_logger

logger = get_logger("search/normativa")

INFOLEG_URL = "https://www.infoleg.gob.ar/infolegInternet/buscarNormas.do"
SAIJ_URL = "https://www.saij.gob.ar/busqueda-de-normas"


async def _scrape_infoleg(query: str, organismo: str = "") -> list:
    """Busca normativa en Infoleg."""
    params = {"palabraContenida": query}
    if organismo:
        params["idOrganismo"] = organismo
    url = f"{INFOLEG_URL}?{urlencode(params)}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    resultados = []
    for fila in soup.select("table.tablaDatos tr")[1:]:
        celdas = fila.find_all("td")
        if len(celdas) < 3:
            continue
        enlace = celdas[1].find("a")
        if not enlace:
            continue
        titulo = enlace.get_text(strip=True)
        href = enlace.get("href", "")
        url_completa = href if href.startswith("http") else f"https://www.infoleg.gob.ar{href}"
        resultados.append({
            "titulo": titulo, "url": url_completa,
            "tipo": celdas[0].get_text(strip=True), "fecha": celdas[2].get_text(strip=True),
        })
    if not resultados:
        for a in soup.select('a[href*="infolegInternet/anexos"]'):
            t = a.get_text(strip=True)
            h = a.get("href", "")
            if t and h:
                resultados.append({"titulo": t, "url": f"https://www.infoleg.gob.ar{h}", "tipo": "Normativa", "fecha": ""})
    return resultados[:10]


async def _scrape_saij(query: str) -> list:
    """Busca normativa en SAIJ."""
    url = f"{SAIJ_URL}?{urlencode({'p': query})}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    resultados = []
    for el in soup.select("article.resultado, li.resultado"):
        enlace = el.select_one("a.titulo-norma, h3 a")
        if not enlace:
            continue
        titulo = enlace.get_text(strip=True)
        href = enlace.get("href", "")
        url_completa = href if href.startswith("http") else f"https://www.saij.gob.ar{href}"
        tipo = el.select_one(".tipo-norma")
        fecha = el.select_one(".fecha")
        resultados.append({
            "titulo": titulo, "url": url_completa,
            "tipo": tipo.get_text(strip=True) if tipo else "Normativa",
            "fecha": fecha.get_text(strip=True) if fecha else "",
        })
    if not resultados:
        for a in soup.select('a[href*="/detalle-norma/"]'):
            t = a.get_text(strip=True)
            h = a.get("href", "")
            if t and h:
                resultados.append({"titulo": t, "url": f"https://www.saij.gob.ar{h}", "tipo": "Normativa", "fecha": ""})
    return resultados[:10]


async def buscar_normativa(query: str, organismo: str = "", **_) -> dict:
    """
    Busca normativa combinando Infoleg y SAIJ en paralelo.

    Returns:
        dict con query, infoleg (list) y saij (list).
    """
    logger.info("Búsqueda normativa query=%s organismo=%s", query, organismo)
    results = await asyncio.gather(
        _scrape_infoleg(query, organismo), _scrape_saij(query), return_exceptions=True,
    )
    infoleg = results[0] if isinstance(results[0], list) else []
    saij = results[1] if isinstance(results[1], list) else []
    if isinstance(results[0], Exception):
        logger.warning("Infoleg falló: %s", str(results[0]))
    if isinstance(results[1], Exception):
        logger.warning("SAIJ falló: %s", str(results[1]))
    return {"query": query, "infoleg": infoleg, "saij": saij}
