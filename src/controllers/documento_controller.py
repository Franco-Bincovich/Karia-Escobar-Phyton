"""
Controller de documentos.
Orquesta la subida y parseo de documentos. Sin lógica de negocio.
"""

import os
import uuid

from fastapi import UploadFile

from src.services.documento_service import parsear_documento
from src.utils.app_error import AppError
from src.utils.logger import get_logger

logger = get_logger("documentoController")


async def subir_documento(file: UploadFile, user: dict) -> dict:
    """
    Guarda el archivo temporalmente, lo parsea y devuelve su texto.

    Args:
        file: Archivo subido vía multipart/form-data.
        user: Usuario autenticado.

    Returns:
        dict con nombre_archivo, tipo, truncado, texto.

    Raises:
        AppError: ARCHIVO_REQUERIDO si no hay archivo.
        AppError: TIPO_NO_SOPORTADO o PARSE_ERROR del service.
    """
    if not file or not file.filename:
        raise AppError("No se recibió ningún archivo.", "ARCHIVO_REQUERIDO", 400)

    # Validar tamaño antes de leer en memoria (20 MB)
    MAX_SIZE = 20 * 1024 * 1024
    contenido = await file.read()
    if len(contenido) > MAX_SIZE:
        raise AppError("Archivo demasiado grande. Máximo 20MB.", "ARCHIVO_DEMASIADO_GRANDE", 413)

    # Guardar temporalmente con nombre único
    ext = os.path.splitext(file.filename)[1].lower()
    ruta_tmp = os.path.join("/tmp", f"{uuid.uuid4()}{ext}")

    try:
        with open(ruta_tmp, "wb") as f:
            f.write(contenido)

        resultado = await parsear_documento(ruta_tmp, file.filename)

        return {
            "nombreArchivo": file.filename,
            "tipo": resultado["tipo"],
            "truncado": resultado["truncado"],
            "texto": resultado["texto"],
        }
    finally:
        # parsear_documento ya borra el archivo, pero por seguridad
        if os.path.exists(ruta_tmp):
            try:
                os.unlink(ruta_tmp)
            except OSError as e:
                logger.warning("No se pudo borrar archivo temporal %s: %s", ruta_tmp, str(e))
