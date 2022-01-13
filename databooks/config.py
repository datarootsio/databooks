"""Configuration functions, and settings objects."""
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import tomli
from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable

from databooks.common import find_common_parent
from databooks.git_utils import get_repo
from databooks.logging import get_logger

TOML_CONFIG_FILE = "pyproject.toml"
INI_CONFIG_FILE = "settings.ini"

ConfigFields = Dict[str, Any]

logger = get_logger(__file__)


def _find_file(filename: str, start: Path, finish: Path) -> Union[Path, None]:
    """
    Recursively find file along directory path, from the end (child) directory to start.

    :param filename: File name to locate
    :param start: Start (parent) directory
    :param finish: Finish (child) directory
    :return: File path
    """
    if not start.is_dir() or not finish.is_dir():
        raise ValueError("Parameters `start` and `finish` must be directory paths.")

    if finish.samefile(start):
        logger.debug(f"No file found between {start} and {finish}.")
        return None
    elif (finish / filename).is_file():
        return finish / filename
    else:
        return _find_file(filename=filename, start=start, finish=finish.parent)


