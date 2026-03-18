from __future__ import annotations

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional


DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    *,
    log_to_file: bool = False,
    log_dir: Optional[Path] = None,
    log_filename: str = "edip.log",
) -> None:
    """
    Configure application-wide logging for EDIP.

    Why this is needed:
    - keeps one shared logging standard across scripts and app modules
    - avoids repeating logging.basicConfig in multiple files
    - supports console logging now and file logging later
    """

    resolved_level = getattr(logging, level.upper(), logging.INFO)

    handlers: dict[str, dict] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level.upper(),
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        }
    }

    root_handler_names = ["console"]

    if log_to_file:
        resolved_log_dir = log_dir or (Path("monitoring") / "logs")
        resolved_log_dir.mkdir(parents=True, exist_ok=True)
        log_path = resolved_log_dir / log_filename

        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": level.upper(),
            "formatter": "standard",
            "filename": str(log_path),
            "encoding": "utf-8",
        }
        root_handler_names.append("file")

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": DEFAULT_LOG_FORMAT,
                "datefmt": DEFAULT_DATE_FORMAT,
            }
        },
        "handlers": handlers,
        "root": {
            "level": resolved_level,
            "handlers": root_handler_names,
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Return a module logger.
    """
    return logging.getLogger(name)


def setup_logging(
    level: str = "INFO",
    *,
    log_to_file: bool = False,
    log_dir: Optional[Path] = None,
    log_filename: str = "edip.log",
) -> None:
    """
    Backward-compatible helper if you prefer setup_logging(...) naming.
    """
    configure_logging(
        level=level,
        log_to_file=log_to_file,
        log_dir=log_dir,
        log_filename=log_filename,
    )