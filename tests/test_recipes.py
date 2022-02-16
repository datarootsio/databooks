from importlib import resources
from pathlib import Path

from databooks.affirm import affirm
from databooks.recipes import CookBook


class TestCookBookGood:
    """Ensure desired effect for recipes."""

    @property
    def nb(self) -> Path:
        """Notebook file for easy access."""
        with resources.path("tests.notebooks", "demo.ipynb") as nb:
            return nb

    def test_has_tags(self) -> None:
        """Ensure that notebook cells have flags."""
        recipe = CookBook.has_tags.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_has_tags_code(self) -> None:
        """Ensure that the code cells have flags."""
        recipe = CookBook.has_tags_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_max_cells(self) -> None:
        """Ensure that notebook has less than 128 cells."""
        recipe = CookBook.max_cells.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_seq_exec(self) -> None:
        """Ensure that the notebook code cells are executed in order."""
        recipe = CookBook.seq_exec.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_seq_increase(self) -> None:
        """Ensure that the notebook code cells are executed monotonically."""
        recipe = CookBook.seq_increase.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_startswith_md(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = CookBook.seq_increase.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_no_empty_code(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = CookBook.no_empty_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False


class TestCookBookBad:
    """Ensure desired effect for recipes."""

    @property
    def nb(self) -> Path:
        """Notebook file for easy access."""
        with resources.path("tests.notebooks", "bad-demo.ipynb") as nb:
            return nb

    def test_has_tags(self) -> None:
        """Ensure that notebook cells have flags."""
        recipe = CookBook.has_tags.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_has_tags_code(self) -> None:
        """Ensure that the code cells have flags."""
        recipe = CookBook.has_tags_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_max_cells(self) -> None:
        """Ensure that notebook has less than 128 cells."""
        recipe = CookBook.max_cells.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_seq_exec(self) -> None:
        """Ensure that the notebook code cells are executed in order."""
        recipe = CookBook.seq_exec.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_seq_increase(self) -> None:
        """Ensure that the notebook code cells are executed monotonically."""
        recipe = CookBook.seq_increase.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_startswith_md(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = CookBook.seq_increase.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_no_empty_code(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = CookBook.no_empty_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False
