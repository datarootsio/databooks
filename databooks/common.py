"""Common set of miscellaneous functions."""
import json
import logging
import os
from itertools import chain
from pathlib import Path
from typing import List

from rich.logging import RichHandler

from databooks import JupyterNotebook


def get_logger(name: str) -> logging.Logger:
    """Get logger with rich configuration."""
    level = os.getenv("LOG_LEVEL", logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    return logging.getLogger(name)


def set_verbose(logger: logging.Logger) -> None:
    """Set logger to DEBUG level when user requests verbosity."""
    verbose_level = logging.DEBUG
    logger.setLevel(verbose_level)
    logger.debug(
        f"Verbose mode: setting log level to {logging.getLevelName(verbose_level)}"
    )


def write_notebook(nb: JupyterNotebook, path: Path) -> None:
    """Write notebook to a path."""
    with path.open("w") as f:
        json.dump(nb.dict(), fp=f, indent=2)


def expand_paths(paths: List[Path], ignore: List[str]) -> List[Path]:
    """
    Get paths of existing file from list of directory or file paths.

    :param paths: Paths to consider (can be directories or files)
    :param ignore: Glob expressions of files to ignore
    :return: List of existing paths for notebooks
    """
    paths = list(
        chain.from_iterable(
            list(path.rglob("*.ipynb")) if path.is_dir() else [path] for path in paths
        )
    )

    return [
        p
        for p in paths
        if not any(p.match(i) for i in ignore) and p.exists() and p.suffix == ".ipynb"
    ]
