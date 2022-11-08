"""Functions to resolve any git conflicts between notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence

from git import Repo

from databooks.common import find_common_parent
from databooks.data_models.notebook import JupyterNotebook
from databooks.git_utils import ConflictFile, get_conflict_blobs, get_repo
from databooks.logging import get_logger, set_verbose

logger = get_logger(__file__)


def path2conflicts(
    nb_paths: List[Path], repo: Optional[Repo] = None
) -> List[ConflictFile]:
    """
    Get the difference model from the path based on the git conflict information.

    :param nb_paths: Path to file with conflicts (must be notebook paths)
    :param repo: The git repo to look for conflicts
    :return: Generator of `DiffModel`s, to be resolved
    """
    if any(nb_path.suffix not in ("", ".ipynb") for nb_path in nb_paths):
        raise ValueError(
            "Expected either notebook files, a directory or glob expression."
        )
    common_parent = find_common_parent(nb_paths)
    repo = get_repo(common_parent) if repo is None else repo
    if repo is None:
        raise ValueError("No repo found - cannot compute conflict blobs.")
    return [
        file
        for file in get_conflict_blobs(repo=repo)
        if any(file.filename.match(str(p.name)) for p in nb_paths)
    ]


def conflict2nb(
    conflict_file: ConflictFile,
    *,
    meta_first: bool = True,
    cells_first: Optional[bool] = None,
    cell_fields_ignore: Sequence[str] = ("id", "execution_count"),
    ignore_none: bool = True,
    verbose: bool = False,
) -> JupyterNotebook:
    """
    Merge diffs from conflicts and return valid a notebook.

    :param conflict_file: A `databooks.git_utils.ConflictFile` with conflicts
    :param meta_first: Whether to keep the metadata of the first or last notebook
    :param cells_first: Whether to keep the cells of the first or last notebook
    :param ignore_none: Keep all metadata fields even if it's included in only one
     notebook
    :param cell_fields_ignore: Fields to remove before comparing notebooks - i.e.: cell
     IDs or execution counts may not want to be considered
    :param verbose: Log written files and metadata conflicts
    :return: Resolved conflicts as a `databooks.data_models.notebook.JupyterNotebook`
     model
    """
    if verbose:
        set_verbose(logger)

    nb_1 = JupyterNotebook.parse_raw(conflict_file.first_contents)
    nb_2 = JupyterNotebook.parse_raw(conflict_file.last_contents)
    if nb_1.metadata != nb_2.metadata:
        msg = (
            f"Notebook metadata conflict for {conflict_file.filename}. Keeping "
            + "first."
            if meta_first
            else "last."
        )
        logger.debug(msg)

    if cell_fields_ignore:
        for cells in (nb_1.cells, nb_2.cells):
            for cell in cells:
                cell.clear_fields(
                    cell_metadata_remove=[], cell_remove_fields=cell_fields_ignore
                )

    diff_nb = nb_1 - nb_2
    nb = diff_nb.resolve(
        ignore_none=ignore_none,
        keep_first=meta_first,
        keep_first_cells=cells_first,
        first_id=conflict_file.first_log,
        last_id=conflict_file.last_log,
    )
    if not isinstance(nb, JupyterNotebook):
        raise RuntimeError(f"Expected `databooks.JupyterNotebook`, got {type(nb)}.")

    logger.debug(f"Resolved conflicts in {conflict_file.filename}.")
    return nb


def conflicts2nbs(
    conflict_files: List[ConflictFile],
    *,
    progress_callback: Callable[[], None] = lambda: None,
    **conflict2nb_kwargs: Any,
) -> None:
    """
    Get notebooks from conflicts.

    Wrap `databooks.conflicts.conflict2nb` to write notebooks to list of
     `databooks.git_utils.ConflictFile`.
    :param conflict_files: Files with source conflict files and one-liner git logs
    :param progress_callback: Callback function to report progress
    :param conflict2nb_kwargs: Keyword arguments to be passed to
     `databooks.conflicts.conflict2nb`
    :return:
    """
    for conflict in conflict_files:
        nb = conflict2nb(conflict, **conflict2nb_kwargs)
        nb.write(path=conflict.filename, overwrite=True)
        progress_callback()
