"""
Cifrado simétrico AES-256-CBC para credenciales de integraciones.
USO EXCLUSIVO de integracion_service — no exponer al frontend.
Formato: iv_hex:ciphertext_hex (compatible con el JS).
"""

import hashlib
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from src.config.index import settings
from src.utils.app_error import AppError

IV_LENGTH = 16
KEY_LENGTH = 32


def _get_salt() -> bytes:
    """Salt derivado del secret — no hardcodeado."""
    return settings.JWT_SECRET[:16].encode() + b":crypto-salt"


def _derivar_clave() -> bytes:
    """Deriva una clave de 32 bytes estable a partir del JWT_SECRET (scrypt)."""
    return hashlib.scrypt(
        settings.JWT_SECRET.encode(), salt=_get_salt(), n=16384, r=8, p=1, dklen=KEY_LENGTH
    )


def cifrar(texto: str) -> str:
    """
    Cifra un texto plano con AES-256-CBC.

    Args:
        texto: Valor a cifrar.

    Returns:
        Cadena con formato "ivHex:cifradoHex".
    """
    clave = _derivar_clave()
    iv = os.urandom(IV_LENGTH)
    padder = PKCS7(128).padder()
    datos = padder.update(texto.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(clave), modes.CBC(iv))
    encryptor = cipher.encryptor()
    cifrado = encryptor.update(datos) + encryptor.finalize()
    return f"{iv.hex()}:{cifrado.hex()}"


def descifrar(valor: str) -> str:
    """
    Descifra un valor cifrado con AES-256-CBC.

    Args:
        valor: Cadena con formato "ivHex:cifradoHex".

    Returns:
        Texto plano descifrado.

    Raises:
        AppError: CRYPTO_FORMAT_ERROR si el formato es inválido.
    """
    if not isinstance(valor, str) or ":" not in valor:
        raise AppError("Credencial con formato inválido", "CRYPTO_FORMAT_ERROR", 500)
    iv_hex, texto_hex = valor.split(":", 1)
    clave = _derivar_clave()
    cipher = Cipher(algorithms.AES(clave), modes.CBC(bytes.fromhex(iv_hex)))
    decryptor = cipher.decryptor()
    datos = decryptor.update(bytes.fromhex(texto_hex)) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return (unpadder.update(datos) + unpadder.finalize()).decode()
