import logging
from importlib import resources

import pytest
from _pytest.logging import LogCaptureFixture

from databooks.affirm import DatabooksParser, affirm
from databooks.data_models.base import DatabooksBase


class TestSafeEval:
    """Test cases for `safe_eval`."""

    def test_basic(self) -> None:
        """Evaluate constant."""
        parser = DatabooksParser()
        assert parser.safe_eval("1") == 1

    def test_local(self) -> None:
        """Evaluate variables."""
        parser = DatabooksParser(a=2)
        assert parser.safe_eval("a") == 2

    def test_local_bool(self) -> None:
        """Evaluate boolean expressions."""
        parser = DatabooksParser(a=2)
        assert parser.safe_eval("a==2") is True

    def test_range(self) -> None:
        """Evaluate built-ins from list of safe nodes."""
        parser = DatabooksParser()
        assert parser.safe_eval("[i*2 for i in range(3)]") == [0, 2, 4]

    def test_range_len(self) -> None:
        """Evaluate built-ins from list of safe nodes."""
        parser = DatabooksParser(l=[1, 2, 3])
        assert parser.safe_eval("[i*2 for i in range(1, len(l))]") == [2, 4]

    def test_comprehension(self) -> None:
        """Variables in expressions should be valid names."""
        parser = DatabooksParser(n=[1, 2, 3])
        assert parser.safe_eval("[i+1 for i in n]") == [2, 3, 4]

    def test_multiply(self) -> None:
        """Multiplications are valid."""
        parser = DatabooksParser()
        assert parser.safe_eval("21 * 2") == 42

    def test_power(self) -> None:
        """Powers are valid."""
        parser = DatabooksParser()
        assert parser.safe_eval("3 ** 3") == 27

    def test_lambda(self) -> None:
        """Expressions in lambda functions raise errors."""
        parser = DatabooksParser()
        with pytest.raises(ValueError):
            parser.safe_eval("lambda: None")

    def test_bad_name(self) -> None:
        """Bad syntax throws errors."""
        parser = DatabooksParser(a=2)
        with pytest.raises(SyntaxError):
            parser.safe_eval("a == None?")

    def test_invalid_attribute(self) -> None:
        """Attributes other than Pydantic fields are invalid."""
        parser = DatabooksParser(a=[2])
        with pytest.raises(ValueError):
            parser.safe_eval("a.__len__")

    def test_valid_attribute(self) -> None:
        """Attributes from Pydantic fields are valid."""
        parser = DatabooksParser(model=DatabooksBase(a=[1, 2, 3]))
        assert parser.safe_eval("model.a") == [1, 2, 3]

    def test_nested_attributes(self) -> None:
        """Nested attributes from Pydantic fields are valid."""
        parser = DatabooksParser(model=DatabooksBase(a=DatabooksBase(b=2)))
        assert parser.safe_eval("model.a.b") == 2

    def test_eval(self) -> None:
        """Trying accessing built-in `eval` raises error."""
        parser = DatabooksParser()
        with pytest.raises(ValueError):
            parser.safe_eval("eval('os.exit()')")

    def test_exit(self) -> None:
        """Trying to exit raises an error."""
        parser = DatabooksParser()
        with pytest.raises(KeyError):
            # `KeyError` is raised since `exit` is an "attribute" of `os`.
            parser.safe_eval("os.exit()")

    def test_exec(self) -> None:
        """Trying to built-in `exec` raises an error."""
        parser = DatabooksParser()
        with pytest.raises(ValueError):
            parser.safe_eval("exec('import os')")

    def test_builtins(self) -> None:
        """Built-ins not white-listed as 'safe' are not accepted."""
        parser = DatabooksParser(__builtins__={"abs": abs})
        with pytest.raises(ValueError):
            parser.safe_eval("abs(-2) == 2")

    def test_dunder_class(self) -> None:
        """Dunder classes are not valid attributes."""
        parser = DatabooksParser()
        with pytest.raises(ValueError):
            parser.safe_eval("().__class__.__bases__[0].__subclasses__()")

    def test_comp_attr(self) -> None:
        """Accessing attributes in comprehensions is valid."""
        parser = DatabooksParser(l=[DatabooksBase(a=1, b=2)] * 2)
        assert parser.safe_eval("[e.a for e in l]") == [1, 1]


def test_affirm(caplog: LogCaptureFixture) -> None:
    """Affirm values in notebooks using string expressions."""
    caplog.set_level(logging.DEBUG)
    with resources.path("tests.files", "demo.ipynb") as nb:
        assert (
            affirm(
                nb,
                [
                    "len(nb.cells) == 6",
                    "len(code_cells) == 5",
                    "len(md_cells) == 1",
                ],
            )
            is True
        )
        assert affirm(nb, ["nb.nbformat == 4"]) is True
        assert affirm(nb, ["any('tags' in c.metadata for c in nb.cells)"]) is False

    logs = list(caplog.records)
    assert len(logs) == 6
    assert logs[-2].message.endswith(" failed 1 of 1 checks.")
    assert logs[-1].message.endswith(
        " failed [\"any('tags' in c.metadata for c in nb.cells)\"]."
    )
