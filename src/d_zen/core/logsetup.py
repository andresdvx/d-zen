"""Logging a archivo rotativo para depuración."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import log_dir


def setup_logging(directory: Path | None = None) -> Path:
    directory = directory or log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "d-zen.log"
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging.getLogger("d_zen").info("D-ZEN iniciado")
    return path
