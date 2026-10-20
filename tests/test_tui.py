import io
from importlib import resources
from textwrap import dedent
from typing import Any

from rich.console import Console

from databooks.data_models.cell import CellMetadata, RawCell
from databooks.data_models.notebook import JupyterNotebook, NotebookMetadata
from databooks.tui import nb2rich
from tests.test_data_models.test_notebook import TestJupyterNotebook

with resources.path("tests.files", "tui-demo.ipynb") as nb_path:
    nb = JupyterNotebook.parse_file(nb_path)

rich_nb = """\
                              Python 3 (ipykernel)
╭────────────────────────────────────────────────╮
│ ╔════════════════════════════════════════════╗ │
│ ║              databooks demo!               ║ │
│ ╚════════════════════════════════════════════╝ │
╰────────────────────────────────────────────────╯
In [1]:
╭────────────────────────────────────────────────╮
│ from random import random  # cell with tags    │
╰────────────────────────────────────────────────╯
In [2]:
╭────────────────────────────────────────────────╮
│ random()                                       │
╰────────────────────────────────────────────────╯
Out [2]:
0.570736084214906
In [3]:
╭────────────────────────────────────────────────╮
│ print("notebooks + git ❤️")                    │
╰────────────────────────────────────────────────╯
notebooks + git ❤️

In [4]:
╭────────────────────────────────────────────────╮
│ throw error                                    │
╰────────────────────────────────────────────────╯
  Cell In [4], line 1
    throw error
          ^
SyntaxError: invalid syntax
╭────────────────────────────────────────────────╮
│ This is a raw cell! 🚀                         │
╰────────────────────────────────────────────────╯
In [5]:
╭────────────────────────────────────────────────╮
│ import pandas as pd                            │
│ import numpy as np                             │
│                                                │
│ print("A dataframe! 🐼")                       │
│ pd.DataFrame(np.random.random((10,3)), columns │
╰────────────────────────────────────────────────╯
A dataframe! 🐼

Out [5]:
                                      \n\
      col0       col1       col2      \n\
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ \n\
  0   0.849474   0.756456   0.268569  \n\
  1   0.511937   0.357224   0.570879  \n\
  2   0.836116   0.928280   0.946514  \n\
  3   0.803129   0.540215   0.335783  \n\
  4   0.074853   0.661168   0.344527  \n\
  5   0.299696   0.782420   0.970147  \n\
  6   0.159906   0.566822   0.243798  \n\
  7   0.896461   0.174406   0.758376  \n\
  8   0.708324   0.895195   0.769364  \n\
  9   0.860726   0.381919   0.329727  \n\
                                      \n\
In [ ]:
╭────────────────────────────────────────────────╮
│                                                │
╰────────────────────────────────────────────────╯
"""


def render(obj: Any, width: int = 50) -> str:
    """Render object to string (instead of terminal)."""
    console = Console(file=io.StringIO(), width=width, legacy_windows=False)
    console.print(obj)
    assert isinstance(console.file, io.StringIO)
    return console.file.getvalue()


def test_code_cell() -> None:
    """Prints code cell with no outputs."""
    assert render(nb.cells[1]) == dedent("""\
In [1]:
╭────────────────────────────────────────────────╮
│ from random import random  # cell with tags    │
╰────────────────────────────────────────────────╯
""")


def test_code_cell_outputs() -> None:
    """Prints code cell with outputs."""
    assert render(nb.cells[2]) == dedent("""\
In [2]:
╭────────────────────────────────────────────────╮
│ random()                                       │
╰────────────────────────────────────────────────╯
Out [2]:
0.570736084214906
""")


def test_code_cell_error() -> None:
    """Prints code cell with errors."""
    assert render(nb.cells[4]) == dedent("""\
In [4]:
╭────────────────────────────────────────────────╮
│ throw error                                    │
╰────────────────────────────────────────────────╯
  Cell In [4], line 1
    throw error
          ^
SyntaxError: invalid syntax
""")


def test_code_cell_df() -> None:
    """Prints code cell data frame and has print statement."""
    assert render(nb.cells[6]) == (
        """\
In [5]:
╭────────────────────────────────────────────────╮
│ import pandas as pd                            │
│ import numpy as np                             │
│                                                │
│ print("A dataframe! 🐼")                       │
│ pd.DataFrame(np.random.random((10,3)), columns │
╰────────────────────────────────────────────────╯
A dataframe! 🐼

Out [5]:
                                      \n\
      col0       col1       col2      \n\
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ \n\
  0   0.849474   0.756456   0.268569  \n\
  1   0.511937   0.357224   0.570879  \n\
  2   0.836116   0.928280   0.946514  \n\
  3   0.803129   0.540215   0.335783  \n\
  4   0.074853   0.661168   0.344527  \n\
  5   0.299696   0.782420   0.970147  \n\
  6   0.159906   0.566822   0.243798  \n\
  7   0.896461   0.174406   0.758376  \n\
  8   0.708324   0.895195   0.769364  \n\
  9   0.860726   0.381919   0.329727  \n\
                                      \n\
"""
    )


def test_md_cell() -> None:
    """Prints markdown cell."""
    assert render(nb.cells[0]) == dedent("""\
╭────────────────────────────────────────────────╮
│ ╔════════════════════════════════════════════╗ │
│ ║              databooks demo!               ║ │
│ ╚════════════════════════════════════════════╝ │
╰────────────────────────────────────────────────╯
""")


def test_raw_cell() -> None:
    """Prints raw cell."""
    assert render(nb.cells[5]) == dedent("""\
╭────────────────────────────────────────────────╮
│ This is a raw cell! 🚀                         │
╰────────────────────────────────────────────────╯
""")


def test_notebook() -> None:
    """Prints notebook (identical to printing all cells)."""
    assert render(nb) == rich_nb


def test_print_nb() -> None:
    """Print notebook from path and add rules with file name."""
    console = Console(file=io.StringIO(), width=50, legacy_windows=False)
    with resources.path("tests.files", "tui-demo.ipynb") as path:
        nb2rich(path, console=console)
    assert isinstance(console.file, io.StringIO)
    assert console.file.getvalue() == "\n".join(
        ("───────────────── tui-demo.ipynb ─────────────────", rich_nb)
    )


def test_diff_nb() -> None:
    """Show rich representation of 'diff' notebook."""
    notebook_1 = TestJupyterNotebook().jupyter_notebook
    notebook_2 = TestJupyterNotebook().jupyter_notebook
    extra_cell = RawCell(
        metadata=CellMetadata(random_meta=["meta"]),
        source="extra",
    )
    notebook_2.cells = notebook_2.cells + [extra_cell]

    diff = notebook_1 - notebook_2
    assert render(diff) == dedent("""\
                               kernel_display_name
In [1]:
╭────────────────────────────────────────────────╮
│ test_source                                    │
╰────────────────────────────────────────────────╯
test text

In [1]:
╭────────────────────────────────────────────────╮
│ test_source                                    │
╰────────────────────────────────────────────────╯
test text

                          ╭──────────────────────╮
         <None>           │ extra                │
                          ╰──────────────────────╯
""")


def test_multiple_diff_nb() -> None:
    """Show rich representation of 'diff' notebook."""
    notebook_1 = TestJupyterNotebook().jupyter_notebook
    notebook_2 = TestJupyterNotebook().jupyter_notebook
    notebook_2.metadata = NotebookMetadata(
        kernelspec=dict(display_name="another_kernel", name="kernel_name"),
    )
    extra_cell = RawCell(
        metadata=CellMetadata(random_meta=["meta"]),
        source="extra",
    )
    notebook_1.cells = notebook_1.cells + [
        RawCell(
            metadata=CellMetadata(),
            source="mod_extra",
        )
    ]
    notebook_2.cells = notebook_2.cells + [extra_cell, extra_cell, extra_cell]

    diff = notebook_1 - notebook_2
    assert render(diff) == dedent("""\
      kernel_display_name           another_kernel
In [1]:
╭────────────────────────────────────────────────╮
│ test_source                                    │
╰────────────────────────────────────────────────╯
test text

In [1]:
╭────────────────────────────────────────────────╮
│ test_source                                    │
╰────────────────────────────────────────────────╯
test text

╭───────────────────────╮ ╭──────────────────────╮
│ mod_extra             │ │ extra                │
╰───────────────────────╯ ╰──────────────────────╯
                          ╭──────────────────────╮
                          │ extra                │
                          ╰──────────────────────╯
                          ╭──────────────────────╮
                          │ extra                │
                          ╰──────────────────────╯
""")
