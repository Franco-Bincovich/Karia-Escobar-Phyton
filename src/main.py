"""
Entry point de la aplicación.
Arranca el servidor Uvicorn apuntando a la instancia de FastAPI definida en app.py.

Ejecutar con:
    uvicorn src.main:app --reload --port 3004
"""

import uvicorn

from src.app import app  # noqa: F401 – re-export para que Uvicorn lo encuentre
from src.config.index import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
