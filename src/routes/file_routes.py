"""
Routing para descarga de archivos generados.
Validación de ownership por userId y prevención de path traversal.
"""

import os

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse

from src.middleware.audit import auditar_accion
from src.middleware.auth import get_current_user
from src.utils.app_error import AppError
from src.utils.logger import get_logger

router = APIRouter(prefix="/api/files", tags=["files"])

logger = get_logger("fileRoutes")

TMP_DIR = "/tmp"

MIME_TYPES = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
    ".csv": "text/csv",
}

ALLOWED_EXTENSIONS = {".xlsx", ".docx", ".pdf", ".csv"}


@router.get("/download")
async def descargar_archivo(
    request: Request,
    filename: str = Query(..., min_length=1, max_length=255),
    user: dict = Depends(get_current_user),
):
    """
    GET /api/files/download?filename=...
    Descarga un archivo generado. Requiere JWT.
    Valida ownership por prefijo {userId}_ y previene path traversal.
    """
    safe_name = os.path.basename(filename)

    if ".." in safe_name or "/" in safe_name or "\\" in safe_name or "\x00" in safe_name:
        raise AppError("Nombre de archivo inválido", "FILENAME_INVALIDO", 400)

    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError("Tipo de archivo no permitido", "TIPO_NO_PERMITIDO", 400)

    if not safe_name.startswith(f"{user['userId']}_"):
        raise AppError("No tenés acceso a este archivo", "FORBIDDEN", 403)

    file_path = os.path.join(TMP_DIR, safe_name)
    resolved = os.path.realpath(file_path)

    if not resolved.startswith(TMP_DIR):
        raise AppError("No tenés acceso a este archivo", "FORBIDDEN", 403)

    if not os.path.isfile(resolved):
        raise AppError("Archivo no encontrado", "FILE_NOT_FOUND", 404)

    media_type = MIME_TYPES.get(ext, "application/octet-stream")
    await auditar_accion(user["userId"], "descarga_archivo", request.client.host, safe_name)
    logger.info("Descarga archivo=%s userId=%s", safe_name, user["userId"])

    return FileResponse(
        path=resolved,
        filename=safe_name,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
