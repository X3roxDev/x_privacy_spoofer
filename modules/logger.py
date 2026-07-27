"""Logging helpers for X Privacy Spoofer."""

from __future__ import annotations

import logging
from logging import Logger

from config import LOG_FILE, ensure_directories


class AppLogger:
    """Central application logger with safe local file output."""

    _logger: Logger | None = None

    @classmethod
    def get_logger(cls) -> Logger:
        """Return a configured logger instance."""
        if cls._logger is not None:
            return cls._logger

        ensure_directories()
        logger = logging.getLogger("x_privacy_spoofer")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not logger.handlers:
            handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        cls._logger = logger
        return logger
