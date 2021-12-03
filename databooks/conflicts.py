"""Functions to resolve any git conflicts between notebooks"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Generator, Optional, cast

from git import Repo

from databooks.common import get_logger, write_notebook
from databooks.data_models.base import BaseCells, DiffModel
from databooks.data_models.notebook import JupyterNotebook
from databooks.git_utils import get_conflict_blobs, get_repo

logger = get_logger(__file__)


class DiffJupyterNotebook(DiffModel):
    """Protocol for mypy static type checking"""

    nbformat: int
    nbformat_minor: int
    metadata: dict[str, Any]
    cells: BaseCells[Any]


@dataclass
class DiffFile:
    filename: Path
    diff_notebook: DiffJupyterNotebook
    first_id: str
    last_id: str


def path2diffs(
    nb_paths: list[Path], repo: Optional[Repo] = None
) -> Generator[DiffFile, None, None]:
    """
    Get the difference model from the path based on the git conflict information
    :param nb_path: Path to file with conflicts (must be glob expression, notebook or
     directory)
    :return: Generator of `DiffModel`s, to be resolved
    """
    if any(nb_path.suffix not in ("", ".ipynb") for nb_path in nb_paths):
        raise ValueError(
            "Expected either notebook files, a directory or glob expression."
        )
    common_parent = max(set.intersection(*[set(p.parents) for p in nb_paths]))
    repo = get_repo(common_parent) if repo is None else repo
    conflict_files = [
        f
        for f in get_conflict_blobs(repo=repo)
        if any(f.filename.match(str(p)) for p in nb_paths)
    ]
    for f in conflict_files:
        nb_1 = JupyterNotebook.parse_raw(f.first_contents)
        nb_2 = JupyterNotebook.parse_raw(f.last_contents)
        yield DiffFile(
            filename=Path(f.filename),
            diff_notebook=cast(DiffJupyterNotebook, nb_1 - nb_2),
            first_id=f.first_log,
            last_id=f.last_log,
        )


def diff2nb(
    diff_file: DiffFile,
    *,
    keep_first: bool = True,
    cells_first: Optional[bool] = None,
    ignore_none: bool = True,
    verbose: bool = False,
) -> JupyterNotebook:
    """
    Merge diffs and return valid a notebook
    :param diff_file: DiffFile with path, DiffJupyterNotebook and IDs
    :param keep_first: Whether to keep the metadata of the first or last notebook
    :param cells_first: Whether to keep the cells of the first or last notebook
    :param ignore_none: Keep all metadata fields even if it's included in only one
     notebook
    :param verbose: Log written files and metadata conflicts
    :return: Resolved conflicts as a `databooks.data_models.notebook.JupyterNotebook`
     model
    """
    first_meta, last_meta = diff_file.diff_notebook.metadata
    if first_meta != last_meta and verbose:
        msg = (
            f"Notebook metadata conflict for {diff_file.filename}. Keeping " + "first."
            if keep_first
            else "last."
        )
        logger.info(msg)
    nb = cast(
        JupyterNotebook,
        diff_file.diff_notebook.resolve(
            ignore_none=ignore_none,
            keep_first=keep_first,
            keep_first_cells=cells_first,
            first_id=diff_file.first_id,
            last_id=diff_file.first_id,
        ),
    )
    nb.remove_fields("is_diff", recursive=True)
    if verbose:
        logger.info(f"Resolved conflicts in {diff_file.filename}.")
    return nb


def diffs2nbs(
    diff_files: list[DiffFile],
    progress_callback: Callable[[], None] = lambda: None,
    **diff2nb_kwargs: Any,
) -> None:
    for diff in diff_files:
        nb = diff2nb(diff, **diff2nb_kwargs)
        write_notebook(nb=nb, path=diff.filename)
        progress_callback()
