"""
Cliente Anthropic singleton (lazy).
Importar desde acá — nunca crear otro cliente.
"""

from functools import lru_cache

from anthropic import Anthropic

from src.config.index import settings


@lru_cache(maxsize=1)
def get_anthropic() -> Anthropic:
    """Retorna el cliente Anthropic singleton."""
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)
