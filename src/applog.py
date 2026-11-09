"""Journalisation locale : fichier tournant dans le dossier de données."""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.storage import db_path

_DONE = False


def log_path():
    return Path(os.environ.get("BIOSPACE_LOG") or db_path().with_name("biospace.log"))


def setup():
    """Configure le logger « biospace » une seule fois. Ne lève jamais d'exception."""
    global _DONE
    if _DONE:
        return
    logger = logging.getLogger("biospace")
    logger.setLevel(logging.INFO)
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(path, maxBytes=500_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())   # dossier en lecture seule : on continue
    _DONE = True
