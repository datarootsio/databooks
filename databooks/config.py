"""Configuration functions, and settings objects."""
from pathlib import Path
from typing import Any, Dict, List, Optional

from databooks.common import find_common_parent
from databooks.git_utils import get_repo
from databooks.logging import get_logger

TOML_CONFIG_FILE = "pyproject.toml"
INI_CONFIG_FILE = "settings.ini"

ConfigFields = Dict[str, Any]

logger = get_logger(__file__)


def _find_file(filename: str, start: Path, finish: Path) -> Optional[Path]:
    """
    Recursively find file along directory path, from the end (child) directory to start.

    :param filename: File name to locate
    :param start: Start (parent) directory
    :param finish: Finish (child) directory
    :return: File path
    """
    if not start.is_dir() or not finish.is_dir():
        raise ValueError("Parameters `start` and `finish` must be directories.")

    if start.resolve() not in [finish, *finish.resolve().parents]:
        logger.debug(
            f"Parameter `start` is not a parent directory of `finish` (for {start} and"
            f" {finish}). Cannot find {filename}."
        )
        return None

    if (finish / filename).is_file():
        return finish / filename
    elif finish.samefile(start):
        logger.debug(f"{filename} not found between {start} and {finish}.")
        return None
    else:
        return _find_file(filename=filename, start=start, finish=finish.parent)


def find_config(target_paths: List[Path], config_filename: str) -> Optional[Path]:
    """Find configuration file from CLI target paths."""
    common_parent = find_common_parent(paths=target_paths)
    repo_dir = get_repo().working_dir

    return _find_file(
        filename=config_filename,
        start=Path(repo_dir) if repo_dir is not None else Path(common_parent.anchor),
        finish=common_parent,
    )
