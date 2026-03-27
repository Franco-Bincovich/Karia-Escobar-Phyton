"""
Logger centralizado.
Formato: [timestamp][LEVEL][module] message
Equivalente al logger Winston del proyecto JS.
"""

import logging
import sys


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def get_logger(module: str) -> logging.Logger:
    """Crea un child logger con el nombre del módulo."""
    logger = logging.getLogger(f"karia.{module}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_build_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger
