"""
Logging configuration setup.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure structured console logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
