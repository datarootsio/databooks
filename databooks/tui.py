"""Terminal user interface (TUI) helper functions and components."""
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path
from typing import List

from rich.columns import Columns
from rich.console import Console
from rich.rule import Rule
from rich.theme import Theme

from databooks.data_models.notebook import JupyterNotebook, NotebookMetadata
from databooks.git_utils import DiffContents

DATABOOKS_TUI = Theme({"in_count": "blue", "out_count": "orange3", "kernel": "bold"})

databooks_console = Console(theme=DATABOOKS_TUI)


def print_nb(path: Path, console: Console = databooks_console) -> None:
    """Show rich representation of notebook in terminal."""
    notebook = JupyterNotebook.parse_file(path)
    console.rule(path.resolve().name)
    console.print(notebook)


def print_nbs(
    paths: List[Path],
    console: Console = databooks_console,
    use_pager: bool = False,
) -> None:
    """Show rich representation of notebooks in terminal."""
    with console.pager(styles=True) if use_pager else nullcontext():  # type: ignore
        for path in paths:
            print_nb(path, console=console)


def print_diff(
    diff: DiffContents,
    console: Console = databooks_console,
) -> None:
    """Show rich representation of notebook diff in terminal."""
    a_nb, b_nb = (
        JupyterNotebook.parse_raw(c)
        if c is not None
        else JupyterNotebook(
            nbformat=0, nbformat_minor=0, metadata=NotebookMetadata(), cells=[]
        )
        for c in (diff.a.contents, diff.b.contents)
    )
    cols = Columns(
        [
            Rule(
                f"{ab}/{c['path'].resolve().name if c['path'] is not None else 'null'}"
            )
            for ab, c in asdict(diff).items()
            if ab in ("a", "b")
        ],
        width=console.width // 2,
        padding=(0, 0),
    )
    console.print(cols, a_nb - b_nb)


def print_diffs(
    diffs: List[DiffContents],
    console: Console = databooks_console,
    use_pager: bool = False,
) -> None:
    """Show rich representation of notebook diff in terminal."""
    with console.pager(styles=True) if use_pager else nullcontext():  # type: ignore
        for diff in diffs:
            print_diff(diff, console=console)
