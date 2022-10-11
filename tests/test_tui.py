import io
from importlib import resources
from textwrap import dedent

from rich.console import Console, ConsoleRenderable

from databooks import JupyterNotebook

with resources.path("tests.files", "demo.ipynb") as nb_path:
    nb = JupyterNotebook.parse_file(nb_path)


def render(obj: ConsoleRenderable, width: int = 50) -> str:
    """Render object to string (instead of terminal)."""
    console = Console(file=io.StringIO(), width=width, legacy_windows=False)
    console.print(obj)
    return console.file.getvalue()


def test_code_cell():
    """Prints code cell with no outputs."""
    assert render(nb.cells[1]) == dedent(
        """In [1]:
╭────────────────────────────────────────────────╮
│ from random import random  # cell with tags    │
╰────────────────────────────────────────────────╯
"""
    )


def test_code_cell_outputs():
    """Prints code cell with no outputs."""
    assert render(nb.cells[2]) == dedent(
        """In [2]:
╭────────────────────────────────────────────────╮
│ random()                                       │
╰────────────────────────────────────────────────╯
Out [2]:
0.9995123767309688
"""
    )
