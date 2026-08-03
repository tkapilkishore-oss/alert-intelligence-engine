"""Centralized logging configuration for Alert Intelligence Engine."""

import logging
import sys
from typing import Optional

from src.constants import DEFAULT_LOG_LEVEL, DEFAULT_LOG_NAME, LOG_FORMAT


def get_logger(name: str = DEFAULT_LOG_NAME, level: Optional[str] = None) -> logging.Logger:
    """Retrieve and configure a project logger instance.

    Args:
        name: Name of the logger instance.
        level: Logging level (e.g. 'INFO', 'WARNING', 'ERROR').

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        log_level = level if level else DEFAULT_LOG_LEVEL
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger
