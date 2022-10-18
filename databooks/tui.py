"""Terminal user interface (TUI) helper functions and components."""
from contextlib import nullcontext
from pathlib import Path
from typing import Any, List

from rich.console import Console
from rich.theme import Theme

from databooks import JupyterNotebook

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
    **kwargs_print_nb: Any
) -> None:
    """Show rich representation of notebooks in terminal."""
    with console.pager(styles=True) if use_pager else nullcontext():  # type: ignore
        for path in paths:
            print_nb(path, console=console, **kwargs_print_nb)
