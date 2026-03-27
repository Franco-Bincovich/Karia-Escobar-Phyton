"""
Configuración de la aplicación FastAPI.
Registra middlewares, rutas y handlers de error.
Acá NO va lógica de negocio.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.index import settings
from src.middleware.error_handler import app_error_handler, generic_error_handler
from src.routes.auth_routes import router as auth_router, limiter
from src.routes.chat_routes import chat_router, conversaciones_router
from src.routes.documento_routes import router as documento_router
from src.routes.funcionalidad_routes import router as funcionalidad_router
from src.routes.integracion_routes import router as integracion_router
from src.utils.app_error import AppError

app = FastAPI(
    title="KarIA Escobar API",
    version="1.0.0",
)

# --- Rate limiter state ---
app.state.limiter = limiter


# --- Security headers ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad a todas las respuestas."""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

# --- Error handlers ---
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, generic_error_handler)

# --- Rutas ---
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversaciones_router)
app.include_router(documento_router)
app.include_router(funcionalidad_router)
app.include_router(integracion_router)


# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "ok"}
