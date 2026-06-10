"""Structured logging setup."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from config.settings import PROJECT_ROOT


def setup_logging(level: str = "INFO") -> logging.Logger:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger("arb_scanner")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_dir / "arb_scanner.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    return root