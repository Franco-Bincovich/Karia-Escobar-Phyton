"""
Configuración centralizada.
ÚNICO lugar donde se leen variables de entorno.
Nunca usar os.environ / os.getenv fuera de este archivo.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Server ---
    PORT: int = 3004
    NODE_ENV: str = "development"  # se mantiene el nombre por compatibilidad con el frontend
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Auth ---
    JWT_SECRET: str = ""

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MAX_CONCURRENT: int = 15

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379"

    # --- Gamma ---
    GAMMA_API_KEY: str = ""

    @property
    def OAUTH_STATE_SECRET(self) -> str:
        """Secret separado para firmar JWT de estado OAuth."""
        return (self.JWT_SECRET or "") + ":oauth-state"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()


def _validar_config() -> None:
    """Verifica que las variables críticas estén configuradas."""
    requeridas = {
        "JWT_SECRET": settings.JWT_SECRET,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_KEY": settings.SUPABASE_KEY,
    }
    faltantes = [k for k, v in requeridas.items() if not v]
    if faltantes:
        raise ValueError(
            f"[Config] Variables de entorno críticas faltantes: {', '.join(faltantes)}. "
            "Revisá tu archivo .env (ver .env.example)."
        )


_validar_config()
