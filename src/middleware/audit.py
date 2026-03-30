"""
Middleware de auditoría para acciones sensibles.
Loguea en formato estructurado: timestamp, user_id, accion, ip, detalle.
"""

from datetime import datetime, timezone

from src.utils.logger import get_logger

logger = get_logger("auditoria")


async def auditar_accion(user_id: str, accion: str, ip: str, detalle: str = "") -> None:
    """
    Registra una acción sensible en el log de auditoría.

    Args:
        user_id: UUID del usuario que realizó la acción.
        accion: Tipo de acción (cambio_password, descarga_archivo).
        ip: Dirección IP del cliente.
        detalle: Información adicional sobre la acción.
    """
    logger.info(
        "AUDIT | timestamp=%s user_id=%s accion=%s ip=%s detalle=%s",
        datetime.now(timezone.utc).isoformat(),
        user_id,
        accion,
        ip,
        detalle or "-",
    )
