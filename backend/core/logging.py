"""Structured server logging.

Configured once at startup. Never logs passwords, tokens, or headers;
exceptions are logged for developers without exposing values to API clients.
"""

import logging
import sys

LOGGER_NAME = "paths"

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger(LOGGER_NAME)
    if _CONFIGURED:
        return logger

    level_name = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level_name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    # Keep uvicorn/access noise at its own level; ours is separate.
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    _CONFIGURED = True
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)