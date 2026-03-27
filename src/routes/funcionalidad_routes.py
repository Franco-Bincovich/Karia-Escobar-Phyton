"""
Routing + validación de entrada para /api/funcionalidades.
Sin lógica de negocio — todo pasa al controller.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.controllers import funcionalidad_controller as ctrl
from src.middleware.auth import get_current_user

router = APIRouter(prefix="/api/funcionalidades", tags=["funcionalidades"])


class CrearFuncionalidadRequest(BaseModel):
    """Body de POST /api/funcionalidades."""
    nombre: str = Field(min_length=1)
    descripcion: str | None = None
    system_prompt: str = Field(min_length=1, max_length=2000)


@router.get("")
async def listar(user: dict = Depends(get_current_user)):
    """GET /api/funcionalidades — lista todas las funcionalidades del usuario."""
    return await ctrl.listar_controller(user)


@router.post("", status_code=201)
async def crear(body: CrearFuncionalidadRequest, user: dict = Depends(get_current_user)):
    """POST /api/funcionalidades — crea una funcionalidad nueva."""
    return await ctrl.crear_controller(body.model_dump(), user)


@router.patch("/{func_id}/toggle")
async def toggle(func_id: str, user: dict = Depends(get_current_user)):
    """PATCH /api/funcionalidades/{func_id}/toggle — alterna activo/inactivo."""
    return await ctrl.toggle_controller(func_id, user)


@router.delete("/{func_id}")
async def eliminar(func_id: str, user: dict = Depends(get_current_user)):
    """DELETE /api/funcionalidades/{func_id} — elimina permanentemente."""
    return await ctrl.eliminar_controller(func_id, user)
