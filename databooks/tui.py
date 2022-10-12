"""Terminal user interface (TUI) helper functions and components."""
from pathlib import Path

from rich.console import Console
from rich.theme import Theme

from databooks import JupyterNotebook

DATABOOKS_TUI = Theme({"in_count": "blue", "out_count": "orange3", "error": "on red"})

databooks_console = Console(theme=DATABOOKS_TUI)


def print_nb(path: Path, console: Console = databooks_console) -> None:
    """Show rich representation notebook in terminal."""
    notebook = JupyterNotebook.parse_file(path)
    console.rule(path.resolve().name)
    console.print(notebook)
