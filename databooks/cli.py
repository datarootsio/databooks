"""Main CLI application"""
from importlib.metadata import metadata
from pathlib import Path
from typing import Optional

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from typer import Argument, Exit, Option, Typer, echo

from databooks.common import expand_paths, get_logger
from databooks.conflicts import diffs2nbs, path2diffs
from databooks.metadata import clear_all

logger = get_logger(__file__)

_DISTRIBUTION_METADATA = metadata("databooks")

app = Typer()


@app.callback()
def callback(version: Optional[bool] = Option(None, "--version")) -> None:
    """
    Data science notebooks - set of helpers to ease collaboration of data scientists
     using Jupyter Notebooks. Easily resolve git conflicts and remove metadata to reduce
     the number of conflicts.
    """
    if version:
        echo("databooks version: " + _DISTRIBUTION_METADATA["Version"])


@app.command()
def meta(
    paths: list[Path] = Argument(..., help="Path(s) or glob expression(s) of files"),
    ignore: list[str] = Option(["!*"], help="Glob expression(s) of files to ignore"),
    prefix: str = Option("", help="Prefix to add to filepath when writing files"),
    suffix: str = Option("", help="Suffix to add to filepath when writing files"),
    rm_outs: bool = Option(False, help="Whether to remove cell outputs"),
    rm_exec: bool = Option(True, help="Whether to remove the cell execution counts"),
    nb_meta_keep: list[str] = Option([], help="Notebook metadata fields to keep"),
    cell_meta_keep: list[str] = Option([], help="Cells metadata fields to keep"),
    overwrite: bool = Option(False, "--yes", "-y", help="Confirm overwrite of files"),
    check: bool = Option(
        False, help="Don't write files but check whether there is unwanted metadata"
    ),
    verbose: bool = Option(False, help="Log processed files in console"),
) -> None:
    """Clear notebook metadata"""
    if any(path.suffix not in ("", ".ipynb") for path in paths):
        raise ValueError(
            "Expected either notebook files, a directory or glob expression."
        )
    nb_paths = expand_paths(paths=paths, ignore=ignore)
    if not bool(prefix + suffix) and not check:
        overwrite = (
            Confirm.ask(
                f"{len(nb_paths)} files may be overwritten"
                " (no prefix nor suffix was passed). Continue?"
            )
            if not overwrite
            else overwrite
        )

        if not overwrite:
            raise Exit()
        else:
            logger.warning(f"{len(nb_paths)} files will be overwritten")

    write_paths = [p.parent / (prefix + p.stem + suffix + p.suffix) for p in nb_paths]
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        metadata = progress.add_task("[yellow]Removing metadata", total=len(nb_paths))

        checks = clear_all(
            read_paths=nb_paths,
            write_paths=write_paths,
            progress_callback=lambda: progress.update(metadata, advance=1),
            notebook_metadata_keep=nb_meta_keep,
            cell_metadata_keep=cell_meta_keep,
            cell_execution_count=rm_exec,
            cell_outputs=rm_outs,
            check=check,
            verbose=verbose,
        )

    if check:
        msg = (
            "No unwanted metadata!"
            if all(checks)
            else f"Found unwanted metadata in {sum(checks)} out of {len(checks)} files"
        )
        logger.info(msg)
    else:
        logger.info(
            f"The metadata of {sum(checks)} out of {len(checks)} notebooks"
            " were removed!"
        )


@app.command()
def fix(
    paths: list[Path] = Argument(
        Path.cwd(), help="Path or glob expression of file with conflicts"
    ),
    ignore: list[str] = Option(["!*"], help="Glob expression(s) of files to ignore"),
    metadata_first: bool = Option(
        True, help="Whether or not to keep the metadata from the first/current notebook"
    ),
    cells_first: Optional[bool] = Option(
        None,
        help="Whether to keep the cells from the first or last notebook."
        " Omit to keep both",
    ),
    interactive: bool = Option(
        False, "--interactive", "-i", help="Interactively resolve the conflicts"
    ),
    verbose: bool = Option(False, help="Log processed files in console"),
) -> None:
    """Fix git conflicts for notebooks"""
    filepaths = expand_paths(paths=paths, ignore=ignore)
    diffs = list(path2diffs(nb_paths=filepaths))
    if not diffs:
        raise ValueError(
            f"No conflicts found at {', '.join([str(p) for p in filepaths])}."
        )
    if interactive:
        raise NotImplementedError

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        conflicts = progress.add_task("[yellow]Removing metadata", total=len(diffs))
        diffs2nbs(
            diff_files=diffs,
            keep_first=metadata_first,
            cells_first=cells_first,
            verbose=verbose,
            progress_callback=lambda: progress.update(conflicts, advance=1),
        )
    logger.info(f"Resolved the conflicts of {len(diffs)}!")


@app.command()
def diff() -> None:
    """Show differences between notebooks"""
    # like git diff but for notebooks
    raise NotImplementedError
