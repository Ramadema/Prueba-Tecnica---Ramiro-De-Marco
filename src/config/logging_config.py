"""Logging configuration."""

import logging
import sys

from src.config.settings import get_settings


def setup_logging() -> None:
    """Configure root logger for the application."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
