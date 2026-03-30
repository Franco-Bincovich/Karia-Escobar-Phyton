"""
Análisis de imágenes y PDFs escaneados usando Claude Vision.
Soporta: JPG, JPEG, PNG, GIF, WEBP, PDF (convertido a imagen).
"""

import base64
import os

from src.integrations.anthropic_client import get_anthropic
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("visionTools")

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
EXTENSIONES_SOPORTADAS = EXTENSIONES_IMAGEN | {".pdf"}
MAX_PAGINAS = 5
MODEL = "claude-sonnet-4-5-20250514"

INSTRUCCION_DEFAULT = (
    "Analizá esta imagen en detalle. Extraé todo el texto visible, "
    "describí el contenido y destacá la información más relevante."
)

MEDIA_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp",
}


def _imagen_a_bloque(ruta: str, ext: str) -> dict:
    """Convierte un archivo de imagen a bloque content de Anthropic."""
    with open(ruta, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": MEDIA_TYPES[ext], "data": data},
    }


def _pdf_a_bloques(ruta: str) -> list[dict]:
    """Convierte cada página de un PDF a bloques de imagen (máx MAX_PAGINAS)."""
    from pdf2image import convert_from_path
    import io

    paginas = convert_from_path(ruta, dpi=200, first_page=1, last_page=MAX_PAGINAS)
    bloques = []
    for pagina in paginas:
        buffer = io.BytesIO()
        pagina.save(buffer, format="PNG")
        data = base64.standard_b64encode(buffer.getvalue()).decode()
        bloques.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": data},
        })
    return bloques


async def analizar_imagen(archivo: str, user_id: str, instruccion: str = "", **_) -> str:
    """
    Analiza imágenes y PDFs escaneados usando Claude Vision.

    Args:
        archivo: Nombre del archivo en /tmp (prefijado con user_id).
        user_id: UUID del usuario autenticado.
        instruccion: Instrucción para el análisis (opcional).

    Returns:
        Texto con el análisis de la imagen.

    Raises:
        AppError: TIPO_NO_SOPORTADO (400) si la extensión no es válida.
        AppError: ARCHIVO_NO_ENCONTRADO (404) si el archivo no existe.
        AppError: VISION_ERROR (500) si Claude no puede procesar la imagen.
    """
    ext = os.path.splitext(archivo)[1].lower()
    if ext not in EXTENSIONES_SOPORTADAS:
        raise AppError(
            f"Formato no soportado: {ext}. Válidos: JPG, PNG, GIF, WEBP, PDF.",
            "TIPO_NO_SOPORTADO", 400,
        )

    ruta = os.path.join("/tmp", f"{user_id}_{archivo}")
    if not os.path.exists(ruta):
        ruta_alt = os.path.join("/tmp", archivo)
        if os.path.exists(ruta_alt):
            ruta = ruta_alt
        else:
            raise AppError(f"Archivo no encontrado: {archivo}", "ARCHIVO_NO_ENCONTRADO", 404)

    try:
        if ext == ".pdf":
            bloques = _pdf_a_bloques(ruta)
        else:
            bloques = [_imagen_a_bloque(ruta, ext)]

        prompt = instruccion.strip() if instruccion and instruccion.strip() else INSTRUCCION_DEFAULT
        content = [*bloques, {"type": "text", "text": prompt}]

        client = get_anthropic()
        respuesta = client.messages.create(
            model=MODEL, max_tokens=4096,
            messages=[{"role": "user", "content": content}],
        )
        texto = "".join(b.text for b in respuesta.content if b.type == "text")
        logger.info("Imagen analizada userId=%s archivo=%s pages=%d", user_id, archivo, len(bloques))
        return texto
    except AppError:
        raise
    except Exception as err:
        logger.error("Error en análisis de imagen: %s", str(err))
        raise AppError(f"No se pudo analizar la imagen: {err}", "VISION_ERROR", 500)
