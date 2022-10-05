from importlib import resources
from pathlib import Path

from databooks.affirm import affirm
from databooks.recipes import CookBook


class TestCookBookGood:
    """Ensure desired effect for recipes."""

    @property
    def nb(self) -> Path:
        """Notebook file for easy access."""
        with resources.path("tests.files", "demo.ipynb") as nb:
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
        recipe = CookBook.startswith_md.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_no_empty_code(self) -> None:
        """Ensure that the notebook contains no empty code cells."""
        recipe = CookBook.no_empty_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is True

    def test_error(self) -> None:
        """Ensure that the notebook's first cell is a markdown cell."""
        recipe = CookBook.seq_exec.src
        with resources.path("tests.files", "doesnt_assert.ipynb") as nb:
            assert affirm(nb_path=nb, exprs=[recipe]) is True


class TestCookBookBad:
    """Ensure desired effect for recipes."""

    @property
    def nb(self) -> Path:
        """Notebook file for easy access."""
        with resources.path("tests.files", "bad-demo.ipynb") as nb:
            return nb

    def test_has_tags(self) -> None:
        """Check fail when notebook cells have no flags."""
        recipe = CookBook.has_tags.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_has_tags_code(self) -> None:
        """Check fail when code cells have no flags."""
        recipe = CookBook.has_tags_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_max_cells(self) -> None:
        """Check fail when notebook has more than 128 cells."""
        recipe = CookBook.max_cells.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_seq_exec(self) -> None:
        """Check fail when notebook code cells are executed out of order."""
        recipe = CookBook.seq_exec.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_seq_increase(self) -> None:
        """Check fail when notebook code cells are not executed monotonically."""
        recipe = CookBook.seq_increase.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_startswith_md(self) -> None:
        """Check fail when notebook's first cell is not a markdown cell."""
        recipe = CookBook.startswith_md.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False

    def test_no_empty_code(self) -> None:
        """Check fail when notebook contains empty code cells."""
        recipe = CookBook.no_empty_code.src
        assert affirm(nb_path=self.nb, exprs=[recipe]) is False
