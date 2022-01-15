"""Common set of miscellaneous functions."""
import json
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional

from databooks import JupyterNotebook
from databooks.logging import get_logger

logger = get_logger(__file__)


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


def find_common_parent(paths: Iterable[Path]) -> Path:
    """Find common parent amongst several file paths."""
    return max(set.intersection(*[set(p.resolve().parents) for p in paths]))


def find_obj(
    obj_name: str, start: Path, finish: Path, is_dir: bool = False
) -> Optional[Path]:
    """
    Recursively find file along directory path, from the end (child) directory to start.

    :param obj_name: File name to locate
    :param start: Start (parent) directory
    :param finish: Finish (child) directory
    :param is_dir: Whether object is a directory or a file
    :return: File path
    """
    if not start.is_dir() or not finish.is_dir():
        raise ValueError("Parameters `start` and `finish` must be directories.")

    if start.resolve() not in [finish, *finish.resolve().parents]:
        logger.debug(
            f"Parameter `start` is not a parent directory of `finish` (for {start} and"
            f" {finish}). Cannot find {obj_name}."
        )
        return None

    is_obj = (finish / obj_name).is_dir() if is_dir else (finish / obj_name).is_file()
    if is_obj:
        return finish / obj_name
    elif finish.samefile(start):
        logger.debug(f"{obj_name} not found between {start} and {finish}.")
        return None
    else:
        return find_obj(obj_name=obj_name, start=start, finish=finish.parent)
