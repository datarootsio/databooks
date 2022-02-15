from importlib import resources
from pathlib import Path

from databooks.affirm import affirm
from databooks.recipes import Recipe


class TestRecipe:
    """Ensure desired effect for recipes."""

    @property
    def nb(self) -> Path:
        """Notebook file for easy access."""
        with resources.path("tests.notebooks", "demo.ipynb") as nb:
            return nb

    def test_has_tags(self) -> None:
        """Ensure that notebook cells have flags."""
        recipe = Recipe.has_tags.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True

    def test_has_tags_code(self) -> None:
        """Ensure that the code cells have flags."""
        recipe = Recipe.has_tags_code.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True

    def test_max_cells(self) -> None:
        """Ensure that notebook has less than 128 cells."""
        recipe = Recipe.max_cells.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True

    def test_seq_exec(self) -> None:
        """Ensure that the notebook code cells are executed in order."""
        recipe = Recipe.seq_exec.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True

    def test_seq_increase(self) -> None:
        """Ensure that the notebook code cells are executed monotonically."""
        recipe = Recipe.seq_increase.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True

    def test_startswith_md(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = Recipe.seq_increase.value
        assert affirm(nb_path=self.nb, exprs=[recipe.src]) is True
