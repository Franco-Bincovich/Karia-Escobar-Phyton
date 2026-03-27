"""
Cliente Supabase singleton (lazy).
Importar desde acá en todos los repositories — nunca crear otro cliente.
Se inicializa en el primer uso para evitar errores cuando las env vars no están seteadas al importar.
"""

from functools import lru_cache

from supabase import create_client, Client

from src.config.index import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Retorna el cliente Supabase singleton. Falla si faltan las env vars."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
