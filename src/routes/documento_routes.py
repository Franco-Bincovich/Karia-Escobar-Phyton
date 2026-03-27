"""
Rutas para subida y parseo de documentos empresariales.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends, Request, UploadFile, File

from src.controllers.documento_controller import subir_documento
from src.middleware.auth import get_current_user
from src.routes.auth_routes import limiter

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


@router.post("/upload")
@limiter.limit("100/15minutes")
async def upload(
    request: Request,
    archivo: UploadFile = File(..., description="Archivo a parsear (PDF, Excel, Word, CSV, TXT)"),
    user: dict = Depends(get_current_user),
):
    """
    POST /api/documentos/upload
    Multipart/form-data con campo "archivo".
    Rate limit: 100 req / 15 min por IP.
    Max file size: 20 MB (controlado por nginx/proxy en prod).
    """
    return await subir_documento(archivo, user)
