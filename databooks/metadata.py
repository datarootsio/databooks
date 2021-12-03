"""Metadata wrapper functions for cleaning notebook metadata"""
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Callable, Optional

from databooks.common import get_logger, write_notebook
from databooks.data_models.notebook import JupyterNotebook

logger = get_logger(__file__)


def clear(
    read_path: Path,
    write_path: Optional[Path] = None,
    notebook_metadata_keep: Sequence[str] = (),
    cell_metadata_keep: Sequence[str] = (),
    check: bool = False,
    verbose: bool = False,
    **kwargs: Any,
) -> bool:
    """
    Clear Jupyter Notebook metadata (at notebook and cell level) and write clean
     notebook. By default remove all metadata.
    :param read_path: Path of notebook file with metadata to be cleaned
    :param write_path: Path of notebook file with metadata to be cleaned
    :param notebook_metadata_keep: Notebook metadata fields to keep
    :param cell_metadata_keep: Cell metadata fields to keep
    :param check: Don't write any files, check whether there is unwanted metadata
    :param verbose: Log written files
    :param kwargs: Additional keyword arguments to pass to
     `databooks.data_models.JupyterNotebook.clear_metadata`
    :return: Whether notebooks contain unwanted metadata
    """

    if write_path is None:
        write_path = read_path
    notebook = JupyterNotebook.parse_file(read_path, content_type="json")

    notebook.clear_metadata(
        notebook_metadata_keep=notebook_metadata_keep,
        cell_metadata_keep=cell_metadata_keep,
        **kwargs,
    )

    nb_equals = notebook == JupyterNotebook.parse_file(read_path, content_type="json")
    if verbose:
        if nb_equals or check:
            msg = (
                "only check (unwanted metadata found)."
                if not nb_equals
                else "no metadata to remove."
            )
            logger.info(f"No action taken for {read_path} - " + msg)
        else:
            write_notebook(nb=notebook, path=write_path)
            logger.info(f"Removed metadata from {read_path}, saved as {write_path}")

    elif not nb_equals:
        write_notebook(nb=notebook, path=write_path)
    return not nb_equals


