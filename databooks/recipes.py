"""Recipe on `databooks assert ...`."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict


@dataclass
class RecipeInfo:
    """Common evaluation strings for `databooks assert ...`."""

    src: str
    description: str


@dataclass
class CookBook:
    """Common user recipes for notebook checks."""

    seq_exec = RecipeInfo(
        src="[c.execution_count for c in exec_cells] =="
        " list(range(1, len(exec_cells) + 1))",
        description="Assert that the executed code cells were executed sequentially"
        " (similar effect to when you 'restart kernel and run all cells').",
    )
    seq_increase = RecipeInfo(
        src="[c.execution_count for c in exec_cells] =="
        " sorted([c.execution_count for c in exec_cells])",
        description="Assert that the executed code cells were executed in increasing"
        " order.",
    )
    has_tags = RecipeInfo(
        src="any(getattr(cell.metadata, 'tags', []) for cell in nb.cells)",
        description="Assert that there is at least one cell with tags.",
    )
    has_tags_code = RecipeInfo(
        src="any(getattr(cell.metadata, 'tags', []) for cell in code_cells)",
        description="Assert that there is at least one code cell with tags.",
    )
    max_cells = RecipeInfo(
        src="len(nb.cells) < 64",
        description="Assert that there are less than 64 cells in the notebook.",
    )
    startswith_md = RecipeInfo(
        src="nb.cells[0].cell_type == 'markdown'",
        description="Assert that the first cell in notebook is a markdown cell.",
    )
    no_empty_code = RecipeInfo(
        src="all(cell.source for cell in code_cells)",
        description="Assert that there are no empty code cells in the notebook.",
    )

    @classmethod
    def _recipes(cls) -> Dict[str, str]:
        """
        Get the recipes as a {`recipe-value`: `recipe-name`} dictionary.

        `Typer` expects the user to pass `Enum.value`, not `Enum.name`.
        """
        names = (attr for attr in dir(cls) if not attr.startswith("_"))
        return {getattr(cls, name).src: name.replace("_", "-") for name in names}


# https://github.com/python/mypy/issues/5317
Recipe = Enum("Recipe", CookBook._recipes())  # type: ignore[misc]
