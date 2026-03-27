"""
Excepción base para errores operacionales.
Equivalente a la clase AppError del proyecto JS.
Formato de respuesta: { error: true, message: str, code: str }
"""


class AppError(Exception):
    """
    Error operacional con código SNAKE_CASE y HTTP status.

    Args:
        message: Descripción legible del error.
        code: Código SNAKE_CASE para el cliente.
        status_code: HTTP status (default 500).
    """

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.is_operational = True
