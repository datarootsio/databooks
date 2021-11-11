"""Common set of miscellaneous functions"""
import logging

from rich.logging import RichHandler


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get logger with rich configuration."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    return logging.getLogger(name)
