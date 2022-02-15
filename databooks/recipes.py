"""Recipe on `databooks assert ...`."""
from dataclasses import dataclass
from enum import Enum


@dataclass
class Flavor:
    """Common evaluation strings for `databooks assert ...`."""

    src: str
    description: str


class Recipe(Enum):
    """Common user recipes for notebook checks."""

    seq_exec = Flavor(
        src="[c.execution_count for c in exec_cells] =="
        " list(range(1, len(exec_cells) + 1))",
        description="Assert that the executed code cells were executed sequentially"
        " (similar effect to when you 'restart kernel and run all cells').",
    )
    seq_increase = Flavor(
        src="[c.execution_count for c in exec_cells] =="
        " sorted([c.execution_count for c in exec_cells])",
        description="Assert that the executed code cells were executed in increasing"
        " order.",
    )
    has_tags = Flavor(
        src="any(hasattr(cell.metadata, 'tags') for cell in nb.cells)",
        description="Assert that there is at least one cell with tags.",
    )
    has_tags_code = Flavor(
        src="any(hasattr(cell.metadata, 'tags') for cell in code_cells)",
        description="Assert that there is at least one code cell with tags.",
    )
    max_cells = Flavor(
        src="len(nb.cells) < 128",
        description="Assert that there are less than 128 cells in the notebook.",
    )
    startswith_md = Flavor(
        src="nb.cells[0].cell_type == 'markdown'",
        description="Assert that the first cell in notebook is a markdown cell.",
    )
