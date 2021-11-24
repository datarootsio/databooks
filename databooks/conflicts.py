"""Functions to resolve any git conflicts between notebooks"""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, cast

from databooks.data_models.base import DiffModel
from databooks.data_models.notebook import JupyterNotebook
from databooks.git_utils import get_conflict_blobs, get_repo


@dataclass
class DiffFile:
    filename: Path
    diff_notebook: DiffModel
    first_id: str
    last_id: str


def path2diff(nb_path: Path) -> Generator[DiffFile, None, None]:
    """
    Get the difference model from the path based on the git conflict information
    :param nb_path: Path to file with conflicts (must be glob expression, notebook or
     directory)
    :return: Generator of `DiffModel`s, to be resolved
    """
    if not (nb_path.suffix in ("", ".ipynb") or nb_path.is_dir()):
        raise ValueError(
            "Expected either notebook fil(s), a directory or glob expression."
        )
    repo = get_repo(nb_path)
    conflict_files = [
        f for f in get_conflict_blobs(repo=repo) if f.filename.match(str(nb_path))
    ]
    for f in conflict_files:
        nb_1 = JupyterNotebook.parse_raw(f.first_contents)
        nb_2 = JupyterNotebook.parse_raw(f.last_contents)
        yield DiffFile(
            filename=Path(f.filename),
            diff_notebook=cast(DiffModel, nb_1 - nb_2),
            first_id=f.first_log,
            last_id=f.last_log,
        )
