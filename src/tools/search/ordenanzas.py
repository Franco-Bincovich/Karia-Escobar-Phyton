"""
Búsqueda de ordenanzas municipales del Partido de Escobar.
"""

from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.tools.search.web import fetch_html
from src.utils.logger import get_logger

logger = get_logger("search/ordenanzas")

BASE_URL = "https://www.escobar.gob.ar/hcd/ordenanzas"


async def buscar_ordenanzas(query: str, **_) -> dict:
    """
    Busca ordenanzas en el sitio del HCD del Partido de Escobar.

    Returns:
        dict con query, fuente y resultados [{numero, titulo, url}].
    """
    logger.info("Búsqueda ordenanzas query=%s", query)
    url = f"{BASE_URL}?buscar={quote_plus(query)}"
    resultados = []

    try:
        html = await fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.select("table tr, .ordenanza-item"):
            enlace = el.find("a")
            titulo = (enlace.get_text(strip=True) if enlace else "") or ""
            titulo = titulo or (el.select_one(".titulo").get_text(strip=True) if el.select_one(".titulo") else "")
            href = enlace.get("href", "") if enlace else ""
            numero_el = el.select_one(".numero, td:first-child")
            numero = numero_el.get_text(strip=True) if numero_el else ""
            if titulo:
                url_completa = href if href.startswith("http") else f"https://www.escobar.gob.ar{href}"
                resultados.append({"numero": numero, "titulo": titulo, "url": url_completa})
    except Exception as err:
        logger.warning("Sitio HCD no disponible: %s", str(err))

    logger.info("Ordenanzas encontradas query=%s cantidad=%d", query, len(resultados))
    return {"query": query, "fuente": "HCD Partido de Escobar", "resultados": resultados[:10]}
